# Release pipeline: long-lived tokens and an unpinned GitHub Action

Status: done
Issue: #73
Files: `.github/workflows/pypi_deploy.yml`, `.github/workflows/tagged_release.yml`

`pypi_deploy.yml` publishes to PyPI with `secrets.PYPI_API_TOKEN` via `uv publish --token` — no OIDC/Trusted Publisher flow, so compromise of that repo secret is enough to publish a malicious release. `tagged_release.yml` uses `secrets.PA_TOKEN` (broader-scoped than `GITHUB_TOKEN`) and pulls `marvinpinto/action-automatic-releases@latest`, an unpinned floating tag that runs with `PA_TOKEN` in scope on every future tagged release with no review. See `docs/security/THREAT_MODEL.md` (Threat 6).

## Work breakdown

- [x] ~~Migrate `pypi_deploy.yml` to PyPI's Trusted Publisher (OIDC) flow, dropping `PYPI_API_TOKEN`~~ superseded — see Resolution
- [ ] Pin `marvinpinto/action-automatic-releases` to a commit SHA instead of `@latest`
- [ ] Evaluate whether `tagged_release.yml` needs `PA_TOKEN`'s scope or can use the default `GITHUB_TOKEN`

## Notes

Both changes are mechanical but touch the actual release path — validate with a pre-release/test tag before relying on them for a real release.

## Resolution

The maintainer decided redtape is no longer published to PyPI at all, so the token-hardening work above for `pypi_deploy.yml` was moot: instead of migrating it to OIDC, the workflow was deleted outright (#73). This removes the `PYPI_API_TOKEN` long-lived-secret risk entirely rather than mitigating it.

`tagged_release.yml` was not coupled to PyPI publishing beyond the `release: created` event that `pypi_deploy.yml` listened for — it contains no PyPI-specific steps or secrets — so it was kept as-is (it still builds artifacts and creates a GitHub release). The remaining `PA_TOKEN` / unpinned-action items in the work breakdown above are still open; they are tracked as general CI-hardening follow-up independent of PyPI removal, not closed by this change.
