# Ralph

An autonomous loop that works through `issues/*.md` one task at a time: it feeds
Claude the open issues + recent commits, lets it implement a single task, run the
feedback loops, and commit — repeating until no AFK tasks remain.

## Files

| File         | Purpose                                                          |
| ------------ | ---------------------------------------------------------------- |
| `afk.sh`     | Sandboxed loop (runs Claude in Docker via Colima). Main entry.   |
| `once.sh`    | Single interactive run on the host (no Docker). For debugging.   |
| `config.sh`  | **The only file you edit per repo** — feedback commands + image. |
| `prompt.md`  | The instructions Claude follows each iteration.                  |

## Porting into another repo

```bash
cp -r ralph /path/to/other-repo/   # copy the whole folder (all 4 files)
cd /path/to/other-repo
mkdir -p issues                    # add your issue *.md files here
$EDITOR ralph/config.sh            # set FEEDBACK_LOOPS + RALPH_IMAGE
```

Then run from anywhere in the repo (the scripts resolve their own paths and
`cd` to the repo root automatically):

```bash
./ralph/afk.sh 10    # up to 10 sandboxed iterations
./ralph/once.sh      # a single interactive run on the host
```

## Configuration (`config.sh`)

- `FEEDBACK_LOOPS` — commands Claude must run before committing (one per array
  entry). Match these to the repo's toolchain, e.g. `pytest`, `cargo test`,
  `go test ./...`. They're injected into `prompt.md` at the `{{FEEDBACK_LOOPS}}`
  placeholder.
- `RALPH_IMAGE` — the Docker image `afk.sh` runs Claude inside. Match it to the
  toolchain (`node:22`, `python:3.12`, …).

## Conventions Ralph expects

- Issues live as markdown files in `issues/` at the repo root.
- Mark an issue **AFK** (autonomous) or **HITL** (human-in-the-loop) — Ralph
  only works AFK issues.
- Completed issues are moved to `issues/done/`; incomplete ones get a progress
  note appended.
- The loop stops when Claude emits `<promise>NO MORE TASKS</promise>`.

## Host requirements

- `colima`, `docker`, `jq`, `git`
- Claude auth available in `~/.claude` (mounted into the container), or
  `ANTHROPIC_API_KEY` exported in your shell.
- `afk.sh` runs `colima start` automatically if the daemon isn't up.
