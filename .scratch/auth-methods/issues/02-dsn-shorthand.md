# DSN string shorthand support

Status: needs-triage

`RedshiftConnector` requires individual env vars (`REDTAPE_HOST`, `REDTAPE_PORT`, etc.). Accepting a single `REDTAPE_URL` DSN (`redshift+psycopg2://user:pass@host:5439/db`) is partially stubbed (`db_url` field) but untested.

## Acceptance criteria

- [ ] Implement `RedshiftConnector.from_dsn(dsn_string)` fully (already exists but untested)
- [ ] Add `REDTAPE_URL` env var support as an alternative to individual vars
- [ ] Add unit tests for DSN parsing (at least: happy path, missing port defaults to 5439, invalid DSN raises ValueError)
