# Redtape

A permission management tool for AWS Redshift, with plans to extend it to other database systems. Inspired by [permifrost](https://gitlab.com/gitlab-data/permifrost/), and [pgbedrock](https://github.com/Squarespace/pgbedrock).

### Repo

Clone this repo and install with `uv`:

```sh
git clone git@github.com:energy-solution/redtape.git redtape
cd redtape
uv sync --group dev
```

### pip / uv, without cloning

Install straight from GitHub:

```sh
pip install git+https://github.com/energy-solution/redtape.git
# or
uv pip install git+https://github.com/energy-solution/redtape.git
```

## Usage

``` sh
❯ redtape run --help
Usage: redtape run [OPTIONS] [SPEC_FILE]

 Run the queries necessary to apply a specification file.

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────╮
│   spec_file      [SPEC_FILE]  A specification or a path to a file containing it. [default: (STDIN)]        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --dry              --no-dry                                               Print changes but do not run     │
│                                                                           them.                            │
│                                                                           [default: no-dry]                │
│ --skip-validate    --no-skip-validate                                     Skip specification file          │
│                                                                           validation.                      │
│                                                                           [default: no-skip-validate]      │
│ --user                                   TEXT                             Apply operations only to users   │
│                                                                           named as provided.               │
│ --group                                  TEXT                             Apply operations only to groups  │
│                                                                           named as provided.               │
│ --operation                              [create|drop|drop_from_group|gr  Apply only provided operations.  │
│                                          ant|revoke|add_to_group|alter_o                                   │
│                                          wner]                                                             │
│ --config                                 PATH                             Path to a Redtape configuration  │
│                                                                           file for database connections.   │
│                                                                           The REDSHIFT_CONFIG environment  │
│                                                                           variable may be set instead.     │
│ --quiet            --no-quiet                                             Show no output except of         │
│                                                                           validation errors, run errors,   │
│                                                                           and queries.                     │
│                                                                           [default: no-quiet]              │
│ --help                                                                    Show this message and exit.      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Connection security (TLS)

`RedshiftConnector` always connects with `sslmode=verify-full` by default, so the
connection is encrypted and the server certificate is verified against a trusted CA —
libpq's own default (`prefer`) would silently allow an unencrypted connection, and
`require` alone does not verify the certificate.

Configure it, like the other connection settings, either through environment
variables or the `.redtape.ini` file (section `redtape.redshift`, pointed to via
`REDTAPE_CONFIG`):

```sh
REDTAPE_REDSHIFT_SSLMODE=verify-full
REDTAPE_REDSHIFT_SSLROOTCERT=/path/to/redshift-ca-bundle.pem
```

```ini
[redtape.redshift]
sslmode = verify-full
sslrootcert = /path/to/redshift-ca-bundle.pem
```

`sslrootcert` should point at the Amazon Redshift CA bundle so the certificate chain
can actually be verified — download it from
[Amazon's Redshift SSL support page](https://docs.aws.amazon.com/redshift/latest/mgmt/connecting-ssl-support.html)
(currently `redshift-ca-bundle.crt`) and reference the local path where you save it.
If `sslrootcert` is left unset, libpq falls back to its own default CA locations,
which may not trust Amazon's CA.

This only covers wire encryption and server verification. It is independent of
authenticating with IAM credentials instead of a password (tracked separately); both
are needed for a fully hardened connection.

## Development

Install dev dependencies once with `uv sync --group dev`, then run tools through `uv` so they resolve against the locked environment (don't call bare `pytest`/`ruff`/`mypy`):

```sh
# Tests
uv run --with pytest pytest tests/ -q                              # unit tests
uv run --with pytest pytest tests/ --cov=redtape --cov-report=term-missing
uv run --with pytest pytest tests/integration/ -m integration -v   # needs a live cluster (docker compose up -d)

# Quality (must be clean before opening a PR)
uv run --with ruff ruff check .          # lint + import sort + format checks
uv run --with ruff ruff format .         # apply formatting
uv run --with mypy mypy redtape/         # strict type check
uv run --with vulture vulture redtape/ whitelist.py --min-confidence 80
```

The integration tests require a running Redshift-compatible database and are skipped by the unit run. See `AGENTS.md` for the full tooling conventions and `docs/adr/0002-code-quality-toolchain.md` for the rationale.

## Specification file

A YAML specification file is used to define groups, users, and their corresponding privileges.

### Privileges: `read`/`write` shorthand

`read` and `write` are the *only* privilege keywords a spec accepts, for both `users` and
`groups` privilege blocks. Raw SQL action names (`select`, `insert`, `drop`, `execute`,
`*_with_grant`, etc.) are rejected outright with an error — they are not silently
ignored or passed through.

Each shorthand expands to a fixed set of underlying grants, per object type:

| Shorthand | Object type | Expands to |
|---|---|---|
| `read` | `table` / `view` | `SELECT` |
| `read` | `schema` | `USAGE` |
| `read` | `database` | `CONNECT` |
| `write` | `table` | `SELECT`, `INSERT`, `UPDATE`, `DELETE` |
| `write` | `schema` | `USAGE`, `CREATE` |
| `write` | `database` | *(no mapping — rejected, see below)* |

`function`, `procedure`, and `language` object types have no `read`/`write` mapping at
all. A spec that declares privileges under any of these is rejected, as is a spec that
declares `database: write:` (there is no shorthand for database-level write).

#### What this removes

Adopting `read`/`write` shorthand as the sole privilege syntax makes the following
permanently inexpressible in a redtape spec (following the precedent set by
[Permifrost](https://gitlab.com/gitlab-data/permifrost/), which made the same
binary read/write trade-off for Snowflake):

- `DROP`, `REFERENCES` on tables (and their `*_WITH_GRANT` variants)
- `TEMPORARY` on databases (and its `*_WITH_GRANT` variant)
- `EXECUTE` on functions/procedures — `function`/`procedure` privileges are entirely
  unsupported
- `USAGE` on languages — `language` privileges are entirely unsupported
- All `*_WITH_GRANT` variants — shorthand has no grant-option concept, so
  `WITH GRANT OPTION` can no longer be expressed in a spec

If any of these are needed later, they require new shorthand vocabulary (e.g. an
`admin:`/`execute:`/`use:` term), not a reintroduction of raw action parsing.

`read`/`write` shorthand is only an *input* format: it is expanded into concrete grants
before validation/diffing and is never stored on the model. `redtape export` still
describes actual database state using raw grant names, since a live cluster's grants
may include ones with no shorthand equivalent (e.g. a lone `SELECT` without the rest of
`write`, or a grant `WITH GRANT OPTION`) — that output is not guaranteed to be
re-parseable as a spec.

Sample:

``` yaml
groups:
    - name: group_name
        privileges:
            table:
                read:
                    - table_name
                    - ...
                write:
                    - table_name
                    - ...

            database:
                read:
                    - database_name
                    - ...

            schema:
                read:
                    - schema_name
                    - ...
                write:
                    - schema_name
                    - ...

roles:
    - name: role_name
        member_of:
            - role_name
            - ...
        privileges:
            table:
                read:
                    - table_name
                    - ...
                write:
                    - table_name
                    - ...

            database:
                read:
                    - database_name
                    - ...

            schema:
                read:
                    - schema_name
                    - ...
                write:
                    - schema_name
                    - ...

users:
    - name: group_name
        is_superuser: boolean
        groups:
            - group_name
            - ...
        roles:
            - role_name
            - ...
        privileges:
            table:
                read:
                    - table_name
                    - ...
                write:
                    - table_name
                    - ...

            database:
                read:
                    - database_name
                    - ...

            schema:
                read:
                    - schema_name
                    - ...
                write:
                    - schema_name
                    - ...

        owns:
            table:
                - table_name
                - ...
            schema:
                - schema_name
                - ...
            database:
                - database_name
                - ...
```

### Passwords are out of scope

`redtape` does not set or store user passwords. Users are created with
`CREATE USER name PASSWORD DISABLE`, which disables password-based login
entirely — the password is never persisted, so it can never leak through a
spec file committed to version control (a spec is normally committed for a
declarative, CI-driven workflow like this one). Provisioning login
credentials for a user (e.g. via IAM/temporary-credential authentication) is
a separate, out-of-band concern; see issue #7.

## Ownership

A user may be declared as the owner of database objects via the `owns:` block.
It is keyed by object type (`table`, `schema`, `database`, ...) and lists the
objects that the user should own. For every declared object `redtape` will run
an `ALTER ... OWNER TO ...` statement so the object's owner matches the spec.

``` yaml
users:
    - name: analytics_owner
      is_superuser: false
      owns:
          table:
              - analytics.public.events
              - analytics.public.sessions
          schema:
              - analytics.public
          database:
              - analytics
```

Given the spec above, `redtape run` will execute, among others:

```
ALTER TABLE analytics.public.events OWNER TO analytics_owner;
ALTER TABLE analytics.public.sessions OWNER TO analytics_owner;
ALTER SCHEMA analytics.public OWNER TO analytics_owner;
ALTER DATABASE analytics OWNER TO analytics_owner;
```

### Requiring an owner for every object

Pass `--require-owner` to `redtape validate` to fail validation unless every
object referenced by a privilege has a declared owner (i.e. appears in some
user's `owns:` block):

``` shell
redtape validate --require-owner spec.yml
```

# To do

`redtape` should be considered in Alpha status: things may break, and test coverage is low. The following tasks are planned for a 1.0.0 release:

- [ ] Meaningfully increase test coverage:
  - [ ] Integration tests against PostgreSQL 8.1 (should closely mimic Redshift).
  - [ ] Unit testing of queries generated.
- [ ] CI/CD:
  - [ ] Remove codecov.
- [ ] Documentation.
- [ ] Missing features:
  - [ ] Support for wildcard (`*`) in specification file.
  - [x] Support for ownership (`ALTER TABLE ... OWNER TO ...`).
  - [ ] Support for roles (`CREATE ROLE`, `GRANT ROLE`, `ASSUMEROLE`, etc...).
  - [ ] Support for role management (`ASSUMEROLE`, `CREATE ROLE`, `DROP ROLE`, etc...).
  - [ ] Support for permissions related to `EXTERNAL` objects.
- [ ] Complete support for `mypy` static type-checking.

# License

MIT
