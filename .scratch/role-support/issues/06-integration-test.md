# Integration test: role support end-to-end

Status: ready-for-agent

Verify that a spec with roles survives a full round-trip against a live database.

## What to build

- Add `tests/integration/test_roles.py`
- Test: apply a spec with a user-defined role → `redtape run` → `redtape export` → assert role appears in exported spec
- Test: remove a role from the spec → `redtape run` → assert role is dropped
- Test: `sys:` roles are present in export but are never dropped by `redtape run`
- Mark any tests that require real Redshift RBAC (unavailable on `heartsim/pgredshift`) with `pytest.mark.skip(reason="requires real Redshift cluster")`

## Acceptance criteria

- [ ] At least one end-to-end test passes against `heartsim/pgredshift` (or is explicitly skipped with a reason)
- [ ] `sys:` role protection is verified in a unit test if the integration environment doesn't support RBAC
- [ ] Tests are discovered by `pytest tests/integration/ -m integration`

## Blocked by

`.scratch/role-support/issues/05-role-operations.md`
