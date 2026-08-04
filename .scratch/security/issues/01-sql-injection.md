# SQL injection: spec-supplied names reach SQL unparameterized

Status: needs-triage
Priority: critical
Issue: #70
Files: `redtape/admin.py:176-246`, `:260-299`, `redtape/connectors.py:413-418`

Every `ManagementOperation.build_*_query` method builds SQL with f-strings/`.format()`, interpolating `subject.name`, `group.name`, and `database_object.name` directly into the statement, executed verbatim via `cursor.execute(query)` with no bind parameters. A crafted user/group/object name in the spec YAML (quote or statement terminator) executes arbitrary SQL with the connector's privileges. See `docs/security/THREAT_MODEL.md` (Threat 1).

## Work breakdown

- [ ] Quote identifiers via `psycopg2.sql.Identifier`/`psycopg2.sql.SQL` composition instead of f-string interpolation in `UserManagementOperation` and `GroupManagementOperation`
- [ ] Add validation on subject/database-object names at spec-load time (reject characters that aren't valid Redshift identifiers) as defense in depth
- [ ] Add regression tests with adversarial names (quotes, semicolons, comment markers)

## Notes

psycopg2 parameter binding doesn't cover identifiers, so this needs `sql.Identifier`-style composition throughout `redtape/admin.py`, not a one-line fix.
