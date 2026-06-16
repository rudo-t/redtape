# sys: system role grants

Status: needs-triage

Redshift ships with built-in system roles (`sys:superuser`, `sys:dba`, `sys:operator`, `sys:secadmin`, `sys:monitor`). These are granted via `GRANT ROLE sys:dba TO ROLE analysts` and cannot be created or dropped.

## Work breakdown

- [ ] Depends on `.scratch/role-support/issues/01-redshift-rbac-roles.md`
- [ ] Ensure `sys:` prefixed roles are never emitted as CREATE/DROP targets
- [ ] Add `iter_sys_role_grants()` to `RedshiftConnector`
- [ ] Add unit test: `sys:` role in desired spec → only GRANT/REVOKE, never CREATE/DROP
