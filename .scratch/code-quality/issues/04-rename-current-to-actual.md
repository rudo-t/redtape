# Rename `current` → `actual` throughout the codebase

Status: ready-for-agent

The domain glossary (CONTEXT.md) uses "actual spec" for the live-database state. The code uses `current` everywhere — `current_spec`, `self.current`, `current_users`, `current_groups`, etc. Align the code with the glossary.

## Affected names

- `DatabaseAdministratorTrainer.current` → `actual`
- `DatabaseAdministratorTrainer.current_spec` parameter → `actual_spec`
- `prepare_*` method parameters: `current_users`, `current_groups` → `actual_users`, `actual_groups`
- Local variables named `current_*` in trainer methods
- Test fixtures and assertions that reference `current_spec`

## Acceptance criteria

- [ ] `grep -r "current_spec\|self\.current\b" redtape/` returns no matches
- [ ] All existing tests pass after the rename
- [ ] No change to runtime behaviour — rename only

## Blocked by

None — can start immediately.
