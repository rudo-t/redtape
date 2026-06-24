# Consolidate Specification.from_redshift_connector into a single connection

Status: needs-triage

`fetch_users_and_groups` opens two connections; `itertools.chain` over three `iter_*` generators opens three more. Loading current spec costs 5 Redshift TCP handshakes (see also bug #12).

## Acceptance criteria

- [ ] Rewrite `from_redshift_connector` to open one connection and run all queries within it
- [ ] Add a test asserting `connector.connect()` is called once per `from_redshift_connector` call
