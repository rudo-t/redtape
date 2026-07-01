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

## Development

Install dev dependencies once with `uv sync --group dev`, then run tools through `uv` so they resolve against the locked environment (don't call bare `pytest`/`ruff`/`mypy`).

### Testing strategy

Tests come in two tiers with different cost and different guarantees:

| Tier | Needs | Speed | CI | What it proves |
|------|-------|-------|----|----------------|
| **Unit** (`tests/`) | nothing — fake connectors | milliseconds | **required**, runs on every PR | The plan and the SQL redtape generates are correct, in isolation. |
| **Integration** (`tests/integration/`) | a real Redshift cluster | seconds + network | **non-blocking**, opt-in | The generated SQL actually applies, and an export round-trips, against Redshift. |

**Unit tests are the gate.** They use fake connectors to assert the operations and SQL produced for a given spec, so they need no database and stay fast. Keep them green; they run on every PR and block merges.

```sh
uv run --with pytest pytest tests/ -q                                # unit tests
uv run --with pytest pytest tests/ --cov=redtape --cov-report=term-missing
```

**Integration tests need a real Redshift cluster.** redtape's read/export path relies on Redshift-only SQL — `svv_external_schemas`, `pg_get_all_external_schemas()`, `VARCHAR(MAX)` — that Postgres and Postgres-based emulators (including pgredshift) do not implement, so they cannot stand in. Point the suite at a test/dev cluster with a libpq DSN; if it is unset or unreachable the suite **skips** (it never errors):

```sh
REDTAPE_INTEGRATION_DSN='host=… port=5439 dbname=… user=… password=…' \
  uv run --with pytest pytest tests/integration/ -m integration -v
```

In CI these run in a dedicated **non-blocking** job (`continue-on-error`, not a required check) using a `REDTAPE_INTEGRATION_DSN` repository secret. The rationale: a cluster can be slow, flaky, or unavailable on forked PRs, and real-cluster coverage shouldn't gate everyday merges — it informs, the unit suite gates. (`docker-compose.yml` provides a local pgredshift container for ad-hoc DDL experiments only; the export tests will not pass against it.)

### Quality gates

These must be clean before opening a PR; CI runs the same checks:

```sh
uv run --with ruff ruff check .          # lint + import sort + format checks
uv run --with ruff ruff format .         # apply formatting
uv run --with mypy mypy redtape/         # strict type check
uv run --with vulture vulture redtape/ whitelist.py --min-confidence 80
```

See `AGENTS.md` for the full tooling conventions and `docs/adr/0002-code-quality-toolchain.md` for the rationale.

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
  - [x] Integration tests wired into CI against a real Redshift cluster (non-blocking). A Postgres emulator can't substitute — see [Testing strategy](#testing-strategy).
  - [ ] Unit testing of queries generated.
- [ ] CI/CD:
  - [ ] Get auto-deployment working again.
  - [x] Remove codecov.
- [ ] Documentation.
- [ ] Missing features:
  - [ ] Support for wildcard (`*`) in specification file.
  - [x] Support for ownership (`ALTER TABLE ... OWNER TO ...`).
  - [ ] Support for roles (`CREATE ROLE`, `GRANT ROLE`, `ASSUMEROLE`, etc.).
  - [ ] Support for permissions related to `EXTERNAL` objects.
- [ ] Complete support for `mypy` static type-checking.

# License

MIT
