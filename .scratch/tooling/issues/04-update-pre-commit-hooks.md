# Update .pre-commit-config.yaml — replace stale hooks

Status: ready-for-agent

`black` is pinned at `21.12b0` (dev deps require `^24.3`), `pre-commit-hooks` is on `v4.0.1`, `detect-secrets` is on `v1.1.0`. flake8 and mypy are in dev deps but absent from pre-commit entirely.

## Target config

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        additional_dependencies: [attrs, cattrs, typer, psycopg2-binary]

  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.11
    hooks:
      - id: vulture
        args: [redtape/, --min-confidence, "80"]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
```

## Notes

Blocked on issue #01 (ruff migration) — remove black/isort hooks before adding ruff hook.
