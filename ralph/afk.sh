#!/bin/bash
set -eo pipefail

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

# Resolve locations so the ralph/ folder can be copied into any repo and run
# from any working directory. The repo root is assumed to be ralph/'s parent.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Per-repo configuration (feedback-loop commands, sandbox image).
source "$SCRIPT_DIR/config.sh"

# jq filter to extract streaming text from assistant messages
stream_text='select(.type == "assistant").message.content[]? | select(.type == "text").text // empty | gsub("\n"; "\r\n") | . + "\r\n\n"'

# jq filter to extract final result
final_result='select(.type == "result").result // empty'

# Render the feedback-loop commands as a markdown list for the prompt.
feedback_list=$(printf -- '- `%s`\n' "${FEEDBACK_LOOPS[@]}")

# Ensure the Colima-backed Docker daemon is running
colima status >/dev/null 2>&1 || colima start

for ((i=1; i<=$1; i++)); do
  tmpfile=$(mktemp)
  trap "rm -f $tmpfile" EXIT

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  issues=$(cat ${ISSUES_GLOB:-issues/*.md} 2>/dev/null || echo "No issues found")
  prompt=$(cat "$SCRIPT_DIR/prompt.md")
  prompt="${prompt/\{\{FEEDBACK_LOOPS\}\}/$feedback_list}"

  docker run --rm -i \
    -v "$PWD":/work -w /work \
    -v "$HOME/.claude":/root/.claude \
    -e ANTHROPIC_API_KEY \
    "$RALPH_IMAGE" npx -y @anthropic-ai/claude-code \
    --verbose \
    --print \
    --output-format stream-json \
    "Previous commits: $commits Issues: $issues $prompt" \
  | grep --line-buffered '^{' \
  | tee "$tmpfile" \
  | jq --unbuffered -rj "$stream_text"

  result=$(jq -r "$final_result" "$tmpfile")

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
