# Issue tracker: Local Markdown

Issues for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- Implementation issues are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/issues/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Feature directories

| Directory | Description |
|---|---|
| `.scratch/bugs/` | Bug fixes (critical, high, low priority) |
| `.scratch/role-support/` | Redshift RBAC roles — highest priority feature |
| `.scratch/wildcard-coverage/` | Database-level and function/procedure wildcards |
| `.scratch/privilege-abstraction/` | `read`/`write` shorthand expansion |
| `.scratch/ownership-enforcement/` | `owns:` / `ALTER_OWNER` end-to-end |
| `.scratch/auth-methods/` | IAM credentials, DSN shorthand |
| `.scratch/modular-specs/` | `!include` directive for splitting specs |
| `.scratch/default-privileges/` | `ALTER DEFAULT PRIVILEGES` support |
| `.scratch/redshift-specific/` | ASSUMEROLE, external schemas, `sys:` roles |
| `.scratch/testing/` | Integration and unit test gaps |
| `.scratch/code-quality/` | Internal refactors and cleanup |
| `.scratch/tooling/` | Linting, type checking, pre-commit toolchain |
