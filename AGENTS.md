# redtape

Declarative Redshift permission management CLI. Reads a YAML spec describing the desired state of users, groups, and privileges; diffs against live Redshift; emits SQL to close the gap.

## Development setup

```bash
uv sync --group dev   # install all dependencies (one-time)
pytest tests/ -v      # run unit tests
pytest tests/ -v --cov=redtape --cov-report=term-missing  # with coverage
pytest tests/integration/ -m integration -v               # integration tests (requires docker compose up -d)
```

## Agent skills

### Issue tracker

Issues live as GitHub issues on the fork `rudo-t/redtape` (always pass `--repo rudo-t/redtape`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-state vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) applied as GitHub labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` at the root and `docs/adr/` for architectural decisions. See `docs/agents/domain.md`.
