# Role operations: CREATE / DROP / GRANT / REVOKE

Status: ready-for-agent

Add `RoleManagementOperation` and wire it into the trainer so `redtape run --dry` shows correct SQL for all role operations.

## What to build

- Add `RoleManagementOperation` to `admin.py` with handlers for:
  - `CREATE ROLE <name>`
  - `DROP ROLE <name>`
  - `GRANT ROLE <role> TO ROLE <other_role>`
  - `REVOKE ROLE <role> FROM ROLE <other_role>`
  - `GRANT ROLE <role> TO USER <user>`
  - `REVOKE ROLE <role> FROM USER <user>`
- Add trainer prepare methods: `prepare_create_roles`, `prepare_drop_roles`, `prepare_grant_role_memberships`, `prepare_revoke_role_memberships`
- `sys:` protection: roles with a `sys:` prefix are never emitted as CREATE or DROP targets, only as GRANT/REVOKE targets
- Wire `RoleManagementOperation` into `DatabaseAdministratorTrainer.train()`

## Acceptance criteria

- [ ] `redtape run --dry spec.yml` shows `CREATE ROLE` for roles in desired but not actual
- [ ] `redtape run --dry spec.yml` shows `DROP ROLE` for roles in actual but not desired
- [ ] `redtape run --dry spec.yml` shows `GRANT ROLE r TO ROLE s` / `GRANT ROLE r TO USER u` for new memberships
- [ ] `redtape run --dry spec.yml` shows `REVOKE ROLE r FROM ROLE s` / `REVOKE ROLE r FROM USER u` for removed memberships
- [ ] `sys:` prefixed roles never appear as CREATE or DROP targets
- [ ] Unit tests cover all six SQL generation paths

## Blocked by

`.scratch/role-support/issues/03-role-model-and-validation.md`
`.scratch/role-support/issues/04-export-roles.md`
