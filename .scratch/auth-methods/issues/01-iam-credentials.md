# IAM / temporary credential auth

Status: needs-triage

Redshift supports IAM auth via `boto3` `get_cluster_credentials`. Static passwords in environment variables are a security anti-pattern for production clusters.

## Work breakdown

- [ ] Add an `auth_mode` setting to `RedshiftConnector` (environ-config): `password` (current) or `iam`
- [ ] In IAM mode, call `boto3.client("redshift").get_cluster_credentials(...)` before connecting; use the returned short-lived credentials
- [ ] Handle credential expiry (15-minute TTL) for long-running `manage()` calls
- [ ] Add unit tests with a mocked boto3 client

## Notes

Requires `boto3` as an optional dependency (`[aws]` extra). Don't add it as a hard dependency.
