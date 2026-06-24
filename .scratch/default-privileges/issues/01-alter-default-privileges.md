# ALTER DEFAULT PRIVILEGES support

Status: needs-triage

`ALTER DEFAULT PRIVILEGES` auto-grants permissions on objects created in the future. Critical for teams where new tables appear constantly. Neither redtape nor permifrost currently handles this.

## Proposed spec format

```yaml
default_privileges:
  - for_user: etl_user
    schema: analytics
    object_type: table
    privileges:
      - select
```

## Work breakdown

- [ ] Add `DefaultPrivilege` model to `specification/models.py`
- [ ] Add `Specification.default_privileges: list[DefaultPrivilege]`
- [ ] Add `DefaultPrivilegeManagementOperation` to `admin.py`
- [ ] Add `iter_default_privileges()` to `RedshiftConnector` (query `pg_default_acl`)
- [ ] Wire into trainer
- [ ] Add unit and integration tests
