# Redtape

A permission management tool for AWS Redshift, with plans to extend it to other database systems. Inspired by [permifrost](https://gitlab.com/gitlab-data/permifrost/), and [pgbedrock](https://github.com/Squarespace/pgbedrock).

## Installing

### Repo

Clone this repo and install with `uv`:

```sh
git clone git@github.com:tomasfarias/redtape.git redtape
cd redtape
uv sync --group dev
```

### PyPI

Install with `pip`:

```sh
python -m pip install redtape-py
```

## Usage

``` sh
❯ redtape run --help
Usage: redtape run [OPTIONS] [SPEC_FILE]

  Run the queries necessary to apply a specification file.

Arguments:
  [SPEC_FILE]  A specification or a path to a file containing it.

Options:
  --dry / --no-dry                Print changes but do not run them.
                                  [default: no-dry]
  --atomic / --no-atomic          Apply the entire run in a single
                                  transaction: abort on the first error and
                                  roll back every change.  [default: no-atomic]
  --skip-validate / --no-skip-validate
                                  Skip specification file validation.
                                  [default: no-skip-validate]
  --user TEXT                     Apply operations only to users named as
                                  provided.
  --group TEXT                    Apply operations only to groups named as
                                  provided.
  --operation [CREATE|DROP|DROP_FROM_GROUP|GRANT|REVOKE|ADD_TO_GROUP]
                                  Apply only provided operations.
  --dbname TEXT                   A Redshift database name to connect to.
  --host TEXT                     The host where a Redshift cluster is
                                  located.
  --port TEXT                     The port where a Redshift cluster is
                                  located.
  --database-user TEXT            A user to connect to Redshift. The user
                                  should have user-management permissions.
  --password TEXT                 The passaword of the given Redshift
                                  username.
  --connection-string TEXT        A connection string to connect to Redshift.
  --quiet / --no-quiet            Show no output except of validation errors,
                                  run errors, and queries.  [default: no-
                                  quiet]
  --help                          Show this message and exit.
```

### Transactional behavior and partial failures

> **⚠️ Without `--atomic`, a failed run can leave your cluster partially changed.**

By default (`--no-atomic`) Redtape applies a run as a best-effort sequence of
statements: it tries to keep going past a failing statement and reports which
ones failed at the end. Once a statement fails, however, the database session's
transaction is aborted, so statements that ran *before* the failure are **not**
durably applied and statements *after* it are skipped. In short: a partially
specified run leaves the cluster in an inconsistent, hard-to-reason-about state,
and Redtape will not automatically retry or clean up.

Use `--atomic` to make the whole run a single transaction:

```sh
redtape run --atomic my-spec.yml
```

With `--atomic` Redtape aborts on the **first** error and rolls back every
change made during the run, so the cluster is left exactly as it was before the
run started. The command exits non-zero and names the operation that failed.
Prefer `--atomic` for unattended or production runs where a half-applied
specification is worse than no change at all.

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

Sample:

``` yaml
groups:
    - name: group_name
        privileges:
            table:
                select:
                    - table_name
                    - ...
                insert:
                    - table_name
                    - ...
                update:
                    - table_name
                    - ...
                drop:
                    - table_name
                    - ...
                delete:
                    - table_name
                    - ...
                references:
                    - table_name
                    - ...

            database:
                create:
                    - database_name
                    - ...
                temporary:
                    - database_name
                    - ...
                temp:
                    - database_name
                    - ...

            schema:
                create:
                    - schema_name
                    - ...
                usage:
                    - schema_name
                    - ...

            function:
                execute:
                    - function_name
                    - ...

            procedure:
                execute:
                    - function_name
                    - ...

            language:
                usage:
                    - language_name
                    - ...

users:
    - name: group_name
        is_superuser: boolean
        member_of:
            - group_name
            - ...
        password:
            type: str
            value: str
        privileges:
            table:
                select:
                    - table_name
                    - ...
                insert:
                    - table_name
                    - ...
                update:
                    - table_name
                    - ...
                drop:
                    - table_name
                    - ...
                delete:
                    - table_name
                    - ...
                references:
                    - table_name
                    - ...

            database:
                create:
                    - database_name
                    - ...
                temporary:
                    - database_name
                    - ...
                temp:
                    - database_name
                    - ...

            schema:
                create:
                    - schema_name
                    - ...
                usage:
                    - schema_name
                    - ...

            function:
                execute:
                    - function_name
                    - ...

            procedure:
                execute:
                    - function_name
                    - ...

            language:
                usage:
                    - language_name
                    - ...
```

# To do

`redtape` should be considered in Alpha status: things may break, and test coverage is low. The following tasks are planned for a 1.0.0 release:

- [ ] Meaningfully increase test coverage:
  - [ ] Integration tests against PostgreSQL 8.1 (should closely mimic Redshift).
  - [ ] Unit testing of queries generated.
- [ ] CI/CD:
  - [ ] Get auto-deployment working again.
  - [ ] Remove codecov.
- [ ] Documentation.
- [ ] Missing features:
  - [ ] Support for wildcard (`*`) in specification file.
  - [ ] Support for ownership (`ALTER TABLE ... OWNER TO ...`).
  - [ ] Support for ownership.
  - [ ] Support for roles (`CREATE ROLE`, `GRANT ROLE`, `ASSUMEROLE`, etc...).
  - [ ] Support for role management (`ASSUMEROLE`, `CREATE ROLE`, `DROP ROLE`, etc...).
  - [ ] Support for permissions related to `EXTERNAL` objects.
- [ ] Complete support for `mypy` static type-checking.

# License

MIT
