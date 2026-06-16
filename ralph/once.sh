#!/bin/bash
set -eo pipefail

# Resolve locations so the ralph/ folder can be copied into any repo and run
# from any working directory. The repo root is assumed to be ralph/'s parent.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Per-repo configuration (feedback-loop commands, sandbox image).
source "$SCRIPT_DIR/config.sh"

# Render the feedback-loop commands as a markdown list for the prompt.
feedback_list=$(printf -- '- `%s`\n' "${FEEDBACK_LOOPS[@]}")

issues=$(cat ${ISSUES_GLOB:-issues/*.md} 2>/dev/null || echo "No issues found")
commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat "$SCRIPT_DIR/prompt.md")
prompt="${prompt/\{\{FEEDBACK_LOOPS\}\}/$feedback_list}"

claude --permission-mode acceptEdits \
  "Previous commits: $commits Issues: $issues $prompt"
