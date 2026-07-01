# redtape

Declarative Redshift permission management CLI. Reads a YAML spec describing the desired state of users, groups, and privileges; diffs against live Redshift; emits SQL to close the gap.

## Development setup

```bash
uv sync --group dev   # install all dependencies (one-time)
```

Run every dev tool through `uv` so it resolves against the locked environment — do **not** call bare `pytest`/`ruff`/`mypy` or use `poetry`:

```bash
# Tests
uv run --with pytest pytest tests/ -q                              # unit tests
uv run --with pytest pytest tests/ --cov=redtape --cov-report=term-missing
uv run --with pytest pytest tests/integration/ -m integration -v   # needs `docker compose up -d`
```

> The 5 integration tests under `tests/integration/` error without a live Redshift cluster
> (`RedshiftConnector.from_dsn`) — see issue #38. The unit suite must stay green.

## Code quality

A single toolchain is configured in `pyproject.toml`. Run all three before opening a PR; they must be clean.

```bash
uv run --with ruff ruff check .          # lint  (ruff replaces black + isort + flake8)
uv run --with ruff ruff format .         # format
uv run --with ruff ruff check --fix .    # auto-fix lint violations
uv run --with mypy mypy redtape/         # type check (strict mode)
uv run --with vulture vulture redtape/ whitelist.py --min-confidence 80   # dead code
```

Conventions:
- **ruff** is the only linter/formatter. Config (`select`, per-file-ignores, `line-length = 88`) lives in `[tool.ruff]`. `E501` and `B008` are intentionally ignored — don't reflow long SQL/Typer strings or rewrite Typer option defaults to satisfy them.
- **mypy** runs with `strict = true`. attrs support is built into mypy's default plugin (do **not** add `plugins = ["mypy.plugins.attrs"]` — that entry point is invalid). A documented `disable_error_code` list in `[tool.mypy]` defers known legacy debt so strict stays on for new code; clear deferred codes as you touch the relevant modules rather than adding new ignores.
- **vulture** runs at `--min-confidence 80`. Dynamic-dispatch callbacks (`@build_query.register` handlers reached via `OperationDispatch`) are recorded in `whitelist.py`; add genuine false positives there rather than lowering the threshold.

> `.pre-commit-config.yaml` runs these same gates as `local` hooks through `uv` (install with `uv run --with pre-commit pre-commit install`); it does not pin external mirror repos that would drift from `pyproject.toml` (closes #45).

## Agent skills

### Issue tracker

Issues live as GitHub issues on the fork `rudo-t/redtape` (always pass `--repo rudo-t/redtape`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-state vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) applied as GitHub labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` at the root and `docs/adr/` for architectural decisions. See `docs/agents/domain.md`.
