"""Integration tests: apply a spec and verify the database state matches."""

from __future__ import annotations

import pytest

from redtape.admin import (
    DatabaseAdministrator,
    DatabaseAdministratorTrainer,
    ManagementOperationError,
    OnError,
)
from redtape.specification import (
    Action,
    DatabaseObject,
    DatabaseObjectType,
    Password,
    PasswordType,
    Privilege,
    Privileges,
    Specification,
    User,
)


@pytest.mark.integration
def test_grant_privilege_applied(connector):
    """GRANT operation reaches the database and shows up in a fresh export."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="test_db.public.pg_tables", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )
    desired_user = User(
        name="redtape_test_user",
        is_superuser=False,
        password=Password(type=PasswordType.PLAIN, value="TestPass1", salt=None),
        privileges=Privileges([priv]),
    )
    desired = Specification(users=[desired_user], groups=[])
    current = Specification.from_redshift_connector(connector)

    trainer = DatabaseAdministratorTrainer(desired_spec=desired, current_spec=current)
    admin = trainer.train()
    success, errors = admin.manage(connector)

    assert success is True
    assert errors == []

    reloaded = Specification.from_redshift_connector(connector)
    reloaded_user = next(
        (u for u in reloaded.users if u.name == "redtape_test_user"), None
    )
    assert reloaded_user is not None
    assert priv in reloaded_user.privileges


@pytest.mark.integration
def test_revoke_privilege_removed(connector):
    """REVOKE operation removes a privilege that was previously granted out-of-band."""
    pytest.skip(
        "requires real Redshift cluster for full out-of-band grant verification"
    )


class _RawOp:
    """A ManagementOperation-shaped object wrapping a raw SQL string.

    DatabaseAdministrator.queries() only needs each op to expose a ``query``
    attribute and a string form, which lets us drive manage() with an
    arbitrary first-succeeds / second-fails pair of statements.
    """

    def __init__(self, query: str):
        self.query = query

    def __str__(self) -> str:
        return f"<RawOp: {self.query}>"


@pytest.mark.integration
def test_atomic_run_rolls_back_first_op_when_second_fails(connector):
    """With OnError.ABORT, a failed second operation rolls back the first (issue #18).

    The first statement creates a user (which would succeed and, without a
    transaction, be committed). The second statement is invalid SQL and fails.
    Under OnError.ABORT the whole run is one transaction, so after the abort
    the user from the first statement must not exist.
    """
    username = "redtape_atomic_rollback_user"

    # Clean up any leftover user from a previous failed run so the CREATE in
    # the first statement is guaranteed to succeed.
    with connector.connect() as conn:
        conn.run_query(f"DROP USER IF EXISTS {username};")

    admin = DatabaseAdministrator(
        ops=[
            _RawOp(f"CREATE USER {username} PASSWORD 'ValidPass1';"),
            # Invalid SQL: guaranteed to raise psycopg2.Error.
            _RawOp("THIS IS NOT VALID SQL;"),
        ]
    )

    with pytest.raises(ManagementOperationError):
        admin.manage(connector, on_error=OnError.ABORT)

    # The first statement's CREATE USER must have been rolled back: the user
    # should not exist after the aborted run. We read pg_user directly (a
    # catalog present on both Redshift and a plain Postgres test container)
    # rather than via from_redshift_connector, which uses Redshift-only
    # columns, so the assertion stays portable.
    with connector.connect() as conn:
        row = conn.run_query(f"SELECT 1 FROM pg_user WHERE usename = '{username}';")
    assert row is None, "CREATE USER was committed; the run was not rolled back"
