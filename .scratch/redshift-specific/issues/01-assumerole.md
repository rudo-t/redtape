# ASSUMEROLE permission support

Status: needs-triage

Needed for `COPY` from S3, `UNLOAD`, and external Lambda functions. Currently not representable in the spec.

## Acceptance criteria

- [ ] Add `ASSUMEROLE` to the `Action` enum
- [ ] Add SQL generation: `GRANT ASSUMEROLE ON '<arn>' TO <user|group> FOR ALL PURPOSES`
- [ ] Add `iter_assumerole_grants()` to `RedshiftConnector`
- [ ] Add to YAML spec documentation with an example

## Notes

This requires a real Redshift cluster to integration-test. Mark integration test `pytest.mark.skip(reason="requires real Redshift cluster")`.
