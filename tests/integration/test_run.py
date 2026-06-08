"""Integration tests: apply a spec and verify the database state matches."""

from __future__ import annotations

import pytest

from redtape.admin import DatabaseAdministratorTrainer
from redtape.specification import (
    Action,
    DatabaseObject,
    DatabaseObjectType,
    Group,
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
    pytest.skip("requires real Redshift cluster for full out-of-band grant verification")
