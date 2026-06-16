# 5 separate connection round-trips to load the current spec

Status: needs-triage
Priority: low

`fetch_users_and_groups` opens two connections; `itertools.chain` over the three `iter_*` generators opens three more. Loading the current spec costs 5 Redshift TCP handshakes.

## Acceptance criteria

- [ ] Consolidate into a single connection with multiple queries (or use a single cursor in sequence)
- [ ] Add a test that asserts `connector.connect()` is called at most once during `Specification.from_redshift_connector()`
