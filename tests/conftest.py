from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager

import pytest
import yaml

import redtape.connectors as db


class FakeRedshiftConnector(db.RedshiftConnector):
    """A configurable stand-in for `redtape.connectors.RedshiftConnector`.

    Subclasses the real `RedshiftConnector` (rather than duck-typing it)
    because `redtape/cli.py`'s `load_spec` does an `isinstance(spec_source,
    RedshiftConnector)` check to pick its loader - a plain look-alike object
    fails that check. Subclassing means this fake needs no live database,
    Docker, or network access:

    - `__init__` never requires real connection credentials (all of
      `RedshiftConnector`'s fields default to `None`).
    - `connect()` is overridden to a no-op context manager, so nothing ever
      calls `psycopg2.connect`.
    - `iter_users`/`iter_groups`/`iter_tables`/`iter_schemas`/
      `iter_databases` are overridden to report whatever rows this fake was
      constructed with, instead of running SQL.

    Each constructor argument takes the corresponding row model from
    `redtape.connectors` (`db.User`, `db.Group`, `db.Table`, `db.Schema`,
    `db.Database`) exactly as `RedshiftConnector`'s real `iter_*` methods
    yield them - including encoding privileges as Redshift ACL strings (see
    `tests/test_specification.py`'s `FakeRedshiftConnector` for worked ACL
    examples). All arguments default to empty, so a test only needs to
    supply what it cares about.

    This is the shared seam for faking a connector in CLI-level tests
    (`redtape run`, `redtape export`): monkeypatch `RedshiftConnector.
    from_environ` to return an instance of this class - see
    `patch_redshift_connector` in `tests/test_cli.py`.
    """

    def __init__(
        self,
        users: Iterable[db.User] = (),
        groups: Iterable[db.Group] = (),
        tables: Iterable[db.Table] = (),
        schemas: Iterable[db.Schema] = (),
        databases: Iterable[db.Database] = (),
    ) -> None:
        super().__init__()
        self._users = list(users)
        self._groups = list(groups)
        self._tables = list(tables)
        self._schemas = list(schemas)
        self._databases = list(databases)

    @contextmanager
    def connect(self) -> Iterator[FakeRedshiftConnector]:
        """No-op replacement for the real, network-touching `connect()`."""
        yield self

    def iter_users(self, ignore_admin: bool = False) -> Iterator[db.User]:
        """Iterate over the configured fake users."""
        yield from self._users

    def iter_groups(self) -> Iterator[db.Group]:
        """Iterate over the configured fake groups."""
        yield from self._groups

    def iter_tables(self, ignore_system: bool = True) -> Iterator[db.Table]:
        """Iterate over the configured fake tables."""
        yield from self._tables

    def iter_schemas(self, ignore_system: bool = True) -> Iterator[db.Schema]:
        """Iterate over the configured fake schemas."""
        yield from self._schemas

    def iter_databases(self, ignore_admin: bool = True) -> Iterator[db.Database]:
        """Iterate over the configured fake databases."""
        yield from self._databases


@pytest.fixture
def fake_connector_factory():
    """Return the `FakeRedshiftConnector` class for building configured fakes.

    Usage:

        def test_something(fake_connector_factory):
            connector = fake_connector_factory(users=[...], groups=[...])
            ...

    Exposed as a fixture (rather than importing the class directly) so
    future test modules can override it if they ever need a different fake
    connector shape, without touching call sites.
    """
    return FakeRedshiftConnector


@pytest.fixture(scope="session")
def spec_file(tmp_path_factory):
    """Create a test configuration file."""
    p = tmp_path_factory.mktemp("config") / "redtape.yml"
    content = yaml.safe_dump(
        {
            "users": [
                {
                    "name": "test_user_1",
                    "is_superuser": True,
                    "groups": ["my_user_group_1", "my_user_group_2"],
                    "privileges": {
                        "table": {
                            "read": [
                                "one_table",
                                "another_table",
                                "database_name.*.*",
                            ],
                        },
                        "schema": {
                            "write": [
                                "a_schema",
                                "database_name.*",
                            ]
                        },
                        "database": {
                            "read": ["my_db"],
                        },
                    },
                }
            ]
        }
    )
    p.write_text(content)
    return p
