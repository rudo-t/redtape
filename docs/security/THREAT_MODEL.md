# Threat model

redtape is a CLI that reads a declarative spec (users, groups, privileges), diffs it
against a live Amazon Redshift cluster, and executes `GRANT`/`REVOKE`/`CREATE`/`DROP`/
`ALTER OWNER` SQL to close the gap. It has no server component and no inbound network
interface — every network interaction is an outbound `psycopg2` connection to a
Redshift cluster the operator already controls. This document describes what redtape
trusts, what it doesn't, and where the gaps are.

## Assets

- **Redshift credentials** — `host`/`port`/`dbname`/`user`/`password`, sourced from
  `.redtape.ini`, `REDTAPE_REDSHIFT_*` env vars, or a `db_url` DSN
  (`redtape/connectors.py:367-411`).
- **Cluster privilege state** — the actual set of users, groups, and grants on the
  target cluster. redtape's whole purpose is to mutate this.
- **New user passwords** — plaintext values in a desired spec's `password:` field,
  destined for a Redshift `CREATE USER ... PASSWORD '...'` statement.
- **The spec file** — the desired-state input. Whoever can get a spec into a `redtape
  run` invocation controls what SQL gets executed.
- **The PyPI package / GitHub release** — `redtape`'s distribution channel
  (`.github/workflows/pypi_deploy.yml`, `.github/workflows/tagged_release.yml`).

## Actors and trust boundaries

- **Operator / CI runner invoking `redtape run`** — trusted. Holds the Redshift
  credentials and decides which spec file to apply.
- **Spec file author** — trusted only as far as your review process makes them.
  `Specification.from_yaml` uses `yaml.safe_load`
  (`redtape/specification/__init__.py:277`), so a spec can't deserialize arbitrary
  Python objects — but nothing downstream sanitizes the *names* inside a spec (see
  Threat 1). Treat spec review the same as code review before it reaches `redtape run`.
- **The Redshift cluster** — an external system redtape connects outbound to. redtape
  does not harden the cluster itself; network exposure, IAM, and VPC configuration are
  the operator's responsibility and out of scope here.
- **GitHub Actions (release pipeline)** — trusted with `PYPI_API_TOKEN` and `PA_TOKEN`.

## Threats

### 1. SQL injection via spec-supplied identifiers (no parameterization)

Every `ManagementOperation.build_*_query` method builds SQL with plain f-strings/
`.format()`, interpolating `subject.name`, `group.name`, `database_object.name`, and
the password directly into the statement — e.g. `build_create_query` and
`build_grant_query` in `redtape/admin.py:176-246`. The result is executed verbatim via
`cursor.execute(query)` with no bind parameters (`redtape/connectors.py:413-418`).

**Scenario:** a spec YAML declares a user or database-object name containing a quote
or a statement terminator (e.g. `alice'; DROP TABLE sensitive; --`). Nothing between
YAML parsing and `cursor.execute` escapes or validates it, so the injected SQL runs
with whatever privileges the configured connector user has.

Redshift/Postgres identifiers can't be bound as query parameters via psycopg2 either
way, so this needs `psycopg2.sql.Identifier`-style quoting rather than parameter
binding — it isn't a one-line fix, which is presumably why it hasn't been done yet.

**Mitigation today:** none in code. The de facto mitigation is treating spec files as
reviewed input (PR review before merge, restricted write access to whatever path
`redtape run` reads from).

### 2. Plaintext passwords leak into logs and terminal output

`Password.__str__` returns the raw plaintext value for `PasswordType.PLAIN`
(`redtape/specification/models.py:256-258`), and `build_create_query` embeds it
directly into `CREATE USER ... PASSWORD '<plaintext>'`
(`redtape/admin.py:183-187`).

That query string is then:
- printed in full during `redtape run --dry` (`redtape/cli.py:191-193`), and
- embedded in the Rich progress descriptions (`f"Running: {query}"`, and the
  success/error variants) during a **real** `redtape run`
  (`redtape/cli.py:215-233`) — not just dry runs.

**Scenario:** a new user's password is written to the terminal, terminal scrollback,
or — if `redtape run` is invoked from CI — the CI job log, in plaintext, on every run
that creates a user. CI logs are frequently retained and more widely readable than the
credentials file itself.

**Mitigation today:** none. If you must set initial passwords via redtape, treat CI
logs for `redtape run` as containing secrets, and rotate any password that appears in
one.

### 3. Credentials at rest have no dedicated secrets-manager path

`RedshiftConnector` reads credentials from an INI file, env vars, or a DSN
(`redtape/connectors.py:367-391`) — all operator-managed, none of them integrated with
a secrets manager (AWS Secrets Manager, Vault, etc.). This is a reasonable default for
a CLI tool, but it means secret hygiene (keeping `.redtape.ini` out of source control,
scoping env vars to the process, rotating the connector's password) is entirely on the
operator; redtape does nothing to help or enforce it.

### 4. No enforced transport encryption to Redshift

`open_connection` calls `psycopg2.connect(dbname=..., host=..., port=..., user=...,
password=...)` (`redtape/connectors.py:482-492`) without an `sslmode` (or
`sslrootcert`). libpq's default (`prefer`) will silently fall back to an unencrypted
connection if the server doesn't require SSL, and even `require` alone doesn't verify
the server certificate. Since the target is usually reached over the internet or a VPC
peering link, this leaves both passive eavesdropping (including the plaintext
passwords from Threat 2, and the connector's own password on the wire) and MITM as
live possibilities, entirely dependent on how the Redshift cluster itself is
configured — redtape doesn't ask for `sslmode=verify-full` either explicitly or via
documentation.

### 5. Partial application on failure (no cross-operation transaction)

Each `ManagementOperation` opens/commits its own connection
(`RedshiftConnector.connect`, `redtape/connectors.py:445-471`), and
`DatabaseAdministrator.manage` runs operations one at a time, catching
`psycopg2.Error` per-operation with `OnError.CONTINUE` as the default
(`redtape/admin.py:715-779`). This is already tracked as a correctness gap
(CONTEXT.md's "Transaction" glossary entry, issue #18), but it's a threat-model
concern too: a plan that fails partway through — whether from a transient DB error or
from Threat 1 being triggered — can leave the cluster in a state that matches neither
the desired nor the prior actual spec, with grants applied out of the order a reviewer
expected. There's no automatic rollback to detect or recover from this.

### 6. Release pipeline: long-lived tokens, one unpinned action

- `pypi_deploy.yml` publishes to PyPI using `secrets.PYPI_API_TOKEN` via `uv publish
  --token`. There's no OIDC/Trusted Publisher flow, so compromise of that repo secret
  is sufficient to publish a malicious `redtape` release. GitHub Actions steps
  (`actions/checkout@v4`, `astral-sh/setup-uv@v5`) are pinned to a version tag, which
  limits — but does not eliminate — the blast radius of a compromised upstream action.
- `tagged_release.yml` uses `secrets.PA_TOKEN` (a personal access token, typically
  broader-scoped than `GITHUB_TOKEN`) to wait for CI and cut the release, and pulls
  `marvinpinto/action-automatic-releases@latest` — an **unpinned** floating tag, so a
  malicious update to that action runs with `PA_TOKEN` in scope on every future tagged
  release with no review of what changed.

**Mitigation today:** steps other than the `@latest` one are pinned to tags (not
SHAs). No Trusted Publisher / OIDC setup for PyPI.

## What redtape gets right (worth preserving, not just gaps)

- `yaml.safe_load` for spec parsing — no arbitrary object deserialization from an
  untrusted-ish spec file.
- No inbound network interface anywhere in the codebase — the entire attack surface
  from the network side is outbound-only, to a cluster the operator already
  provisioned and trusts.
- `Password.validate()` enforces a minimum complexity bar (length, upper/lower/digit)
  for plaintext passwords before they'd reach `CREATE USER`
  (`redtape/specification/models.py:271-314`).

## Out of scope

- Redshift-side IAM, VPC/security-group configuration, and cluster encryption
  settings — these are the operator's responsibility; redtape connects to a
  cluster that already exists.
- OS-level protection of `.redtape.ini` / env vars (file permissions, CI secret
  masking) — standard secrets hygiene, not something redtape's code can enforce.
- Postgres support (#27) and RBAC roles (#32) — both explicitly post-MVP per
  CONTEXT.md; this threat model covers what's implemented today (users, groups,
  privileges) and should be revisited when either lands.
