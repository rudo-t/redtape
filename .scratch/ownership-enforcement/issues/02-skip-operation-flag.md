# Add `--skip-operation` (denylist) to `run`

Status: needs-triage
Issue: #66

`redtape run` only supports `--operation` as an *allowlist*. Expressing "everything except ownership" (the common least-privilege CI case) means enumerating every other `Operation` member by hand, which drifts silently whenever a new operation is added to the enum.

## Work breakdown

- [ ] Add `--skip-operation: list[Operation] | None` to `run` in `redtape/cli.py`
- [ ] Wire into `filter_operations` as a denylist; define precedence when combined with `--operation`
- [ ] Unit tests: single skip, multiple skips, interaction with `--operation`
- [ ] Document in README with the least-privilege CI example

## Notes

Superseded as *the* answer to "default run must not require superuser" by #67 (opt-in ownership), but remains a reasonable general denylist ergonomic — cross-link the two.
