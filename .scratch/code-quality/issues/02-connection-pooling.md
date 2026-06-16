# Connection pooling / reuse in RedshiftConnector

Status: needs-triage

`manage()` opens a new psycopg2 connection for every SQL statement (see bug #01). Fix that first, then consider whether a proper connection pool (`psycopg2.pool.SimpleConnectionPool`) is warranted for concurrent use cases.

## Acceptance criteria

- [ ] Blocked on `.scratch/bugs/issues/01-connection-per-statement.md`
- [ ] Single connection for full `manage()` run as a minimum
- [ ] Connection pool as a follow-up if concurrent use cases are identified
