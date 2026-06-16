# PostgresConnector — extend redtape to support standard Postgres

Status: needs-triage

The README states redtape has "plans to extend to other database systems." The architecture already supports this — `DatabaseConnector` is an abstract base class and `RedshiftConnector` extends it. Adding Postgres support is mostly isolated to the connector layer.

## What to build

Add a `PostgresConnector` class that implements `DatabaseConnector` without Redshift-specific catalog views:

- Replace `svv_external_schemas` and `pg_get_shared_redshift_schemas()` in `iter_schemas` with standard `information_schema.schemata`
- Replace Redshift-specific catalog joins with standard `pg_catalog` equivalents
- Default port 5432 (vs Redshift's 5439)
- Handle password type differences: Postgres uses MD5 and SCRAM-SHA-256; `SHA256` and `DISABLED` types are Redshift-only and should not be offered for Postgres grantees
- Add `--db-type [redshift|postgres]` flag to the CLI (or auto-detect from port/DSN)

## What does NOT need to change

- `Specification`, `User`, `Group`, `Privilege` models — already database-agnostic
- SQL generation in `admin.py` — standard Postgres SQL throughout; works on both
- The plan/operation model — no changes needed

## Acceptance criteria

- [ ] `PostgresConnector` passes the same `iter_*` interface as `RedshiftConnector`
- [ ] `redtape export` and `redtape run --dry` work against a standard Postgres 14+ database
- [ ] Redshift-specific password types (SHA256, DISABLED) are rejected by `validate` when `--db-type postgres` is set
- [ ] Redshift-specific operations (ASSUMEROLE, external schemas) are not emitted for Postgres targets
- [ ] Integration tests run against a `postgres:14` container (separate docker-compose service)

## Out of scope

- Redshift RBAC roles — Postgres has roles natively but via a different mechanism (`CREATE ROLE`, `GRANT ROLE TO USER`). This overlaps with `.scratch/role-support/` and should be coordinated.
- MySQL, SQLite, other databases — one connector at a time.

## Blocked by

None — can start immediately, but coordinate with `.scratch/role-support/` since Postgres native roles and Redshift RBAC roles have different SQL syntax.
