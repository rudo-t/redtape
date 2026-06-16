# Redshift RBAC role support

Status: needs-triage
Priority: highest

Redshift added `CREATE ROLE`, `GRANT ROLE TO ROLE`, and `sys:` system roles in 2022. Redtape has no `Role` model, no SQL generation, and no spec format support. This is the largest functional gap for any modern Redshift cluster.

## Work breakdown

- [ ] Add `Role` to `specification/models.py` (name, member_of, privileges)
- [ ] Add `Specification.roles: list[Role]`
- [ ] Add role-to-role `member_of` support in the spec YAML
- [ ] Add `RoleManagementOperation` to `admin.py` (CREATE ROLE, DROP ROLE, GRANT ROLE TO ROLE)
- [ ] Wire `RoleManagementOperation` into `DatabaseAdministratorTrainer` prepare methods
- [ ] Add `iter_roles()` to `RedshiftConnector`
- [ ] Handle `sys:` system roles (read-only, never dropped)
- [ ] Add unit tests for all of the above
- [ ] Add integration test: create a role, grant it to a user, verify via export

## Notes

`sys:` system roles (e.g. `sys:superuser`) are pre-existing on any cluster and must never be emitted as CREATE/DROP targets. The diff engine needs to skip them on the desired side if they don't exist in current (or treat them as always-present).
