# Export roles from a live database

Status: ready-for-agent

Add `iter_roles()` to `RedshiftConnector` so `redtape export` includes roles in the output YAML.

## What to build

- Add `iter_roles()` to `RedshiftConnector` — query `pg_roles` / `svv_roles` for user-defined roles and `svv_role_grants` for role-to-role and user-to-role memberships
- Filter out `sys:`-prefixed roles from the CREATE/DROP candidates (read them into the actual spec but mark them as system roles so the trainer never emits CREATE/DROP for them)
- Wire `iter_roles()` into `Specification.from_redshift_connector()`
- Update `redtape export` output to include the `roles:` section

## Acceptance criteria

- [ ] `redtape export` produces a YAML with a `roles:` section containing all user-defined roles
- [ ] `sys:` prefixed roles appear in the actual spec but are never emitted as CREATE/DROP targets
- [ ] Role-to-role and user-to-role memberships are correctly reflected in the exported spec
- [ ] Unit tests use a mock cursor; no live DB required

## Blocked by

`.scratch/role-support/issues/03-role-model-and-validation.md`
