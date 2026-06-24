# No transactional rollback on partial failure

Status: needs-triage
Priority: low

Each query is committed immediately. A failed run leaves the database in a partially-applied state with no way to roll back.

## Acceptance criteria

- [ ] Document this limitation prominently in the README
- [ ] Consider a `--atomic` flag that aborts on first error via `OnError.ABORT` and rolls back the entire run
- [ ] If `--atomic` is implemented, add an integration test: apply a spec where the second operation will fail; assert the first operation's effects are rolled back
