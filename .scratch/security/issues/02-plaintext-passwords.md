# Plaintext passwords leak into run/dry-run output and CI logs

Status: done
Priority: critical
Issue: #71
Files: `redtape/specification/models.py:256-258`, `redtape/admin.py:183-187`, `redtape/cli.py:191-233`

`Password.__str__` returns the raw plaintext value for `PasswordType.PLAIN`, and `build_create_query` embeds it directly into `CREATE USER ... PASSWORD '<plaintext>'`. That query string is printed in full during `redtape run --dry` and embedded in Rich progress descriptions during a real run, so any run that creates a user with a plaintext password writes that password to the terminal and to CI job logs. See `docs/security/THREAT_MODEL.md` (Threat 2).

## Work breakdown

- [x] ~~Redact password values before a query is ever passed to `console_print`/progress callbacks~~ superseded — see Resolution
- [x] Decide whether redtape should manage plaintext passwords at all in CI-invoked runs, or push provisioning to an out-of-band mechanism (IAM auth, see #7) — decided: it should not
- [x] ~~Add a test asserting no plaintext password substring appears in anything passed to a print/progress callback~~ moot, there's no password to redact

## Notes

Raised alongside a broader discussion of whether CI-driven password management belongs in redtape at all, given IAM/temporary-credential auth (#7) is the safer pattern for CI-invoked deploys.

## Resolution

Redaction doesn't fix the actual problem: a spec YAML with a plaintext password committed to version control exposes that password in git history regardless of what's redacted from runtime output. The maintainer decided to remove password management from redtape entirely rather than harden the leak. `CREATE USER` now always emits `PASSWORD DISABLE` (verified against Redshift docs — disables password-based login, restricts the user to IAM/temporary-credential auth). The `Password`/`PasswordType` model, the `password:` spec field, and all related validation/serialization were removed. Password provisioning is out of scope for redtape going forward; see issue #7 for the intended IAM-auth path.
