# Stand up heartsim/pgredshift in CI

Status: needs-triage

Integration tests exist under `tests/integration/` but are never run in CI. The `docker-compose.yml` is ready; it just needs a GitHub Actions job.

## Acceptance criteria

- [ ] Add `.github/workflows/test.yml` (or extend an existing one) with a `services:` block for `heartsim/pgredshift` on port 5439
- [ ] Run `pytest tests/integration/ -m integration` as a separate CI step
- [ ] Document which tests require a real Redshift cluster and mark them `pytest.mark.skip(reason="requires real Redshift cluster")`

## Notes

`docker-compose.yml` already has the correct image, port mapping, and healthcheck. The CI job only needs to replicate the `environment:` block as service env vars.
