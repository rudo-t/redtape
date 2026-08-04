# No enforced TLS / certificate verification on Redshift connections

Status: needs-triage
Issue: #72
Files: `redtape/connectors.py:482-492`

`RedshiftConnector.open_connection` calls `psycopg2.connect(...)` without `sslmode` or `sslrootcert`. libpq's default (`prefer`) silently falls back to an unencrypted connection if the server doesn't require SSL, and `require` alone doesn't verify the server certificate. See `docs/security/THREAT_MODEL.md` (Threat 4).

## Work breakdown

- [ ] Add `sslmode` (default `verify-full`) and `sslrootcert` settings to `RedshiftConnector` (environ-config)
- [ ] Document how to point `sslrootcert` at the Amazon Redshift CA bundle
- [ ] Add a config test asserting the default connect args request verified TLS

## Notes

Independent of #7 (IAM auth) — that replaces the password, this replaces wire encryption/verification. Both are needed for a hardened connection.
