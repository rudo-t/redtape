# Release pipeline: long-lived tokens and an unpinned GitHub Action

Status: needs-triage
Issue: #73
Files: `.github/workflows/pypi_deploy.yml`, `.github/workflows/tagged_release.yml`

`pypi_deploy.yml` publishes to PyPI with `secrets.PYPI_API_TOKEN` via `uv publish --token` — no OIDC/Trusted Publisher flow, so compromise of that repo secret is enough to publish a malicious release. `tagged_release.yml` uses `secrets.PA_TOKEN` (broader-scoped than `GITHUB_TOKEN`) and pulls `marvinpinto/action-automatic-releases@latest`, an unpinned floating tag that runs with `PA_TOKEN` in scope on every future tagged release with no review. See `docs/security/THREAT_MODEL.md` (Threat 6).

## Work breakdown

- [ ] Migrate `pypi_deploy.yml` to PyPI's Trusted Publisher (OIDC) flow, dropping `PYPI_API_TOKEN`
- [ ] Pin `marvinpinto/action-automatic-releases` to a commit SHA instead of `@latest`
- [ ] Evaluate whether `tagged_release.yml` needs `PA_TOKEN`'s scope or can use the default `GITHUB_TOKEN`

## Notes

Both changes are mechanical but touch the actual release path — validate with a pre-release/test tag before relying on them for a real release.
