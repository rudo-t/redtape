# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub issues on the fork **`rudo-t/redtape`**. Use the `gh` CLI for all operations.

> **Always pass `--repo rudo-t/redtape`.** This clone's `origin` points at the upstream `tomasfarias/redtape`, so `gh` would otherwise default to upstream. Every command below pins the fork explicitly.

## Conventions

- **Create an issue**: `gh issue create --repo rudo-t/redtape --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --repo rudo-t/redtape --comments`.
- **List issues**: `gh issue list --repo rudo-t/redtape --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --repo rudo-t/redtape --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --repo rudo-t/redtape --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --repo rudo-t/redtape --comment "..."`

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `rudo-t/redtape`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --repo rudo-t/redtape --comments`.
