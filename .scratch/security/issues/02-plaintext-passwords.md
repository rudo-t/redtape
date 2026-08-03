# Plaintext passwords leak into run/dry-run output and CI logs

Status: needs-triage
Priority: critical
Issue: #71
Files: `redtape/specification/models.py:256-258`, `redtape/admin.py:183-187`, `redtape/cli.py:191-233`

`Password.__str__` returns the raw plaintext value for `PasswordType.PLAIN`, and `build_create_query` embeds it directly into `CREATE USER ... PASSWORD '<plaintext>'`. That query string is printed in full during `redtape run --dry` and embedded in Rich progress descriptions during a real run, so any run that creates a user with a plaintext password writes that password to the terminal and to CI job logs. See `docs/security/THREAT_MODEL.md` (Threat 2).

## Work breakdown

- [ ] Redact password values before a query is ever passed to `console_print`/progress callbacks
- [ ] Decide whether redtape should manage plaintext passwords at all in CI-invoked runs, or push provisioning to an out-of-band mechanism (IAM auth, see #7) — evaluate before redacting, since redaction doesn't address spec-authoring-time exposure
- [ ] Add a test asserting no plaintext password substring appears in anything passed to a print/progress callback

## Notes

Raised alongside a broader discussion of whether CI-driven password management belongs in redtape at all, given IAM/temporary-credential auth (#7) is the safer pattern for CI-invoked deploys.
