# One psycopg2 connection opened per SQL statement

Status: needs-triage
Priority: critical
File: `admin.py:751`

`manage()` opens, commits, and closes a new TCP connection for every GRANT/REVOKE/CREATE statement. 50 operations = 50 handshakes to Redshift.

## Acceptance criteria

- [ ] Batch all operations into a single connection context for the full run
- [ ] Commit at the end (or use a savepoint per statement for partial-failure handling)
- [ ] Add a test that asserts `connector.connect()` is called exactly once during `manage()`
