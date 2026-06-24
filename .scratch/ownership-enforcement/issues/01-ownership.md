# Ownership enforcement — test, document, and harden

Status: needs-triage

The spec supports `owns:` and `ALTER_OWNER` is implemented in SQL generation, but there are no integration tests and it is not documented in the README.

## Work breakdown

- [ ] Write an integration test: declare `owns:` for a user, run redtape, assert `ALTER TABLE ... OWNER TO ...` is executed
- [ ] Document `owns:` in the README with an example spec
- [ ] Add a `require_owner` validation flag: `validate` fails if any object in the spec has no declared owner
- [ ] Add a unit test: `ALTER_OWNER` query generation for TABLE, SCHEMA, DATABASE

## Notes

`ALTER_OWNER` is on the `feat/schema-wildcard` branch. Check that it survived the rebase onto `fix/revoke-arg-order` cleanly before writing tests.
