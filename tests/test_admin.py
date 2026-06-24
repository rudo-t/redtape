"""Unit tests for the admin module."""

from __future__ import annotations

from unittest import mock

import pytest

from redtape.admin import (
    DatabaseAdministratorTrainer,
    GroupManagementOperation,
    ManagementOperation,
    OperationDispatch,
    UserManagementOperation,
)
from redtape.specification import (
    Action,
    DatabaseObject,
    DatabaseObjectType,
    Group,
    Operation,
    Ownerships,
    Password,
    PasswordType,
    Privilege,
    Privileges,
    Specification,
    User,
)


@pytest.fixture
def select_privilege():
    """Provide a select Privilege model for testing."""
    priv = Privilege(
        database_object=DatabaseObject(name="one_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    return priv


@pytest.fixture
def create_privilege():
    """Provide a create Privilege model for testing."""
    priv = Privilege(
        database_object=DatabaseObject(name="a_schema", type=DatabaseObjectType.SCHEMA),
        action=Action.CREATE,
    )
    return priv


@pytest.fixture
def user():
    """Provide a User model for testing."""
    user = User(
        name="test_user_1",
        is_superuser=False,
        member_of={"a_user_group_1", "a_user_group_2"},
        password=Password(type=PasswordType.PLAIN, value="aplainpassword", salt=None),
    )
    return user


@pytest.fixture
def group():
    """Provide a Group model for testing."""
    group = Group(
        name="a_user_group_1",
        privileges=None,
    )
    return group


def test_user_management_operation_create_user(user):
    """Test the build_query method for a CREATE operation."""
    op = UserManagementOperation(
        operation=Operation.CREATE,
        subject=user,
        privilege=None,
    )

    result = op.build_query()
    expected = (
        "CREATE USER test_user_1 PASSWORD 'aplainpassword';"  # pragma: allowlist secret
    )

    assert result == expected


def test_user_management_operation_drop(user):
    """Test the build_query method for a DROP operation."""
    op = UserManagementOperation(
        operation=Operation.DROP,
        subject=user,
        privilege=None,
    )

    result = op.build_query()
    expected = "DROP USER test_user_1;"

    assert result == expected


def test_user_management_operation_add_to_group(user, group):
    """Test the build_query method for an ADD_TO_GROUP operation."""
    op = UserManagementOperation(
        operation=Operation.ADD_TO_GROUP,
        subject=user,
        privilege=None,
        group=group,
    )

    result = op.build_query()
    expected = "ALTER GROUP a_user_group_1 ADD USER test_user_1;"

    assert result == expected

    op = UserManagementOperation(
        operation=Operation.ADD_TO_GROUP,
        subject=user,
        privilege=None,
    )

    with pytest.raises(TypeError):
        result = op.build_query()


def test_user_management_operation_drop_from_group(user, group):
    """Test the build_query method for a drop_from_group operation."""
    op = UserManagementOperation(
        operation=Operation.DROP_FROM_GROUP,
        subject=user,
        privilege=None,
        group=group,
    )

    result = op.build_query()
    expected = "ALTER GROUP a_user_group_1 DROP USER test_user_1;"

    assert result == expected

    op = UserManagementOperation(
        operation=Operation.ADD_TO_GROUP,
        subject=user,
        privilege=None,
    )

    with pytest.raises(TypeError):
        result = op.build_query()


def test_user_management_operation_grant(user, select_privilege, create_privilege):
    """Test the build_query method for grant operation."""
    op = UserManagementOperation(
        operation=Operation.GRANT,
        subject=user,
        privilege=select_privilege,
    )

    result = op.build_query()
    expected = "GRANT SELECT ON TABLE one_table TO test_user_1;"

    assert result == expected


def test_user_management_operation_grant_with_wildcard(user):
    """Test the build_query method for grant operation with a wildcard."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="my_db.my_schema.*", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )

    op = UserManagementOperation(
        operation=Operation.GRANT,
        subject=user,
        privilege=priv,
    )

    result = op.build_query()
    expected = "GRANT SELECT ON ALL TABLES IN SCHEMA my_db.my_schema TO test_user_1;"

    assert result == expected


def test_user_management_operation_grant_without_privilege_raises_typeerror(user):
    """GRANT with privilege=None should raise TypeError, not NameError."""
    op = UserManagementOperation(
        operation=Operation.GRANT,
        subject=user,
        privilege=None,
    )

    with pytest.raises(TypeError):
        op.build_query()


def test_group_management_operation_create(group):
    """Test the build_query method for a CREATE operation."""
    op = GroupManagementOperation(
        operation=Operation.CREATE,
        subject=group,
        privilege=None,
    )

    result = op.build_query()
    expected = "CREATE GROUP a_user_group_1;"

    assert result == expected


def test_group_management_operation_drop(group):
    """Test the build_query method for a DROP operation."""
    op = GroupManagementOperation(
        operation=Operation.DROP,
        subject=group,
        privilege=None,
    )

    result = op.build_query()
    expected = "DROP GROUP a_user_group_1;"

    assert result == expected


def test_group_management_operation_grant(group, select_privilege, create_privilege):
    """Test the build_query method for grant operation."""
    op = GroupManagementOperation(
        operation=Operation.GRANT,
        subject=group,
        privilege=select_privilege,
    )

    result = op.build_query()
    expected = "GRANT SELECT ON TABLE one_table TO a_user_group_1;"

    assert result == expected


def test_group_management_operation_grant_with_wildcard(group):
    """Test the build_query method for grant operation with a wildcard."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="my_db.my_schema.*", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )

    op = GroupManagementOperation(
        operation=Operation.GRANT,
        subject=group,
        privilege=priv,
    )

    result = op.build_query()
    expected = "GRANT SELECT ON ALL TABLES IN SCHEMA my_db.my_schema TO a_user_group_1;"

    assert result == expected


def test_group_management_operation_grant_without_privilege_raises_typeerror(group):
    """GRANT with privilege=None should raise TypeError, not NameError."""
    op = GroupManagementOperation(
        operation=Operation.GRANT,
        subject=group,
        privilege=None,
    )

    with pytest.raises(TypeError):
        op.build_query()


def test_group_management_operation_repr(group):
    """repr() on a GroupManagementOperation should not raise (issue #14)."""
    op = GroupManagementOperation(
        operation=Operation.CREATE,
        subject=group,
        privilege=None,
    )
    result = repr(op)
    assert result.startswith("GroupManagementOperation(")
    assert "operation=" in result
    assert "subject=" in result


def test_group_management_operation_invalid(group):
    """Test the build_query method for an invalid Group operation."""
    invalid_1 = GroupManagementOperation(
        operation=Operation.ADD_TO_GROUP,
        subject=group,
    )
    invalid_2 = GroupManagementOperation(
        operation=Operation.DROP_FROM_GROUP,
        subject=group,
    )

    with pytest.raises(ValueError):
        invalid_1.build_query()

    with pytest.raises(ValueError):
        invalid_2.build_query()


def test_trainer_revoke_removes_extra_user_privilege():
    """Trainer should emit REVOKE for privileges in current but not in desired."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="secret_table", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )
    current_user = User(name="alice", is_superuser=False, privileges=Privileges([priv]))
    desired_user = User(name="alice", is_superuser=False, privileges=Privileges([]))

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[current_user], groups=[]),
    )
    admin = trainer.train()

    revoke_ops = [op for op in admin.ops if op.operation is Operation.REVOKE]
    assert len(revoke_ops) == 1
    assert revoke_ops[0].privilege == priv
    assert revoke_ops[0].subject.name == "alice"


def test_trainer_revoke_removes_extra_group_privilege():
    """Trainer should emit REVOKE for group privileges in current but not in desired."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="secret_table", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )
    current_group = Group(name="analysts", privileges=Privileges([priv]))
    desired_group = Group(name="analysts", privileges=Privileges([]))

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[], groups=[desired_group]),
        current_spec=Specification(users=[], groups=[current_group]),
    )
    admin = trainer.train()

    revoke_ops = [op for op in admin.ops if op.operation is Operation.REVOKE]
    assert len(revoke_ops) == 1
    assert revoke_ops[0].privilege == priv
    assert revoke_ops[0].subject.name == "analysts"


def test_trainer_no_revoke_for_desired_privilege():
    """Trainer should NOT emit REVOKE for privileges that are in the desired spec."""
    priv = Privilege(
        database_object=DatabaseObject(
            name="allowed_table", type=DatabaseObjectType.TABLE
        ),
        action=Action.SELECT,
    )
    user = User(name="alice", is_superuser=False, privileges=Privileges([priv]))

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[user], groups=[]),
        current_spec=Specification(users=[user], groups=[]),
    )
    admin = trainer.train()

    revoke_ops = [op for op in admin.ops if op.operation is Operation.REVOKE]
    assert len(revoke_ops) == 0


def test_schema_wildcard_grant_expands_to_all_schemas():
    """A wildcard schema privilege in the desired spec expands to individual schemas."""
    wildcard_priv = Privilege(
        database_object=DatabaseObject(name="mydb.*", type=DatabaseObjectType.SCHEMA),
        action=Action.USAGE,
    )
    user = User(
        name="alice", is_superuser=False, privileges=Privileges([wildcard_priv])
    )

    current_spec = Specification(
        users=[User(name="alice", is_superuser=False, privileges=Privileges([]))],
        groups=[],
        schema_names={"mydb": ["public", "analytics", "raw"]},
    )

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[user], groups=[]),
        current_spec=current_spec,
    )
    admin = trainer.train()

    grant_ops = [op for op in admin.ops if op.operation is Operation.GRANT]
    granted_names = {op.privilege.database_object.name for op in grant_ops}

    assert granted_names == {"mydb.public", "mydb.analytics", "mydb.raw"}


def test_schema_wildcard_revoke_removes_all_schemas():
    """Removing a wildcard schema privilege revokes each individual schema."""
    public_priv = Privilege(
        database_object=DatabaseObject(
            name="mydb.public", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.USAGE,
    )
    analytics_priv = Privilege(
        database_object=DatabaseObject(
            name="mydb.analytics", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.USAGE,
    )
    current_user = User(
        name="alice",
        is_superuser=False,
        privileges=Privileges([public_priv, analytics_priv]),
    )
    desired_user = User(name="alice", is_superuser=False, privileges=Privileges([]))

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(
            users=[current_user],
            groups=[],
            schema_names={"mydb": ["public", "analytics"]},
        ),
    )
    admin = trainer.train()

    revoke_ops = [op for op in admin.ops if op.operation is Operation.REVOKE]
    revoked_names = {op.privilege.database_object.name for op in revoke_ops}

    assert revoked_names == {"mydb.public", "mydb.analytics"}


def test_schema_wildcard_no_expand_without_schema_names():
    """Wildcard schema with no schema_names in current spec passes through unexpanded."""
    wildcard_priv = Privilege(
        database_object=DatabaseObject(name="mydb.*", type=DatabaseObjectType.SCHEMA),
        action=Action.USAGE,
    )
    user = User(
        name="alice", is_superuser=False, privileges=Privileges([wildcard_priv])
    )

    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[user], groups=[]),
        current_spec=Specification(users=[user], groups=[]),
    )
    admin = trainer.train()

    grant_ops = [op for op in admin.ops if op.operation is Operation.GRANT]
    assert len(grant_ops) == 0


def test_operation_dispatch():
    class FakeManagementOperation(ManagementOperation):
        dispatch = OperationDispatch()

        def __init__(self, operation):
            self.operation = operation

        @dispatch.register(Operation.CREATE)
        def handle_create(self) -> str:
            return "CREATE"

        @dispatch.register(Operation.DROP)
        def handle_drop(self) -> str:
            return "DROP"

        @dispatch.register(Operation.ADD_TO_GROUP)
        def handle_add_to_group(self) -> str:
            return "ADD_TO_GROUP"

        @dispatch.register(Operation.DROP_FROM_GROUP)
        def handle_drop_from_group(self) -> str:
            return "DROP_FROM_GROUP"

        @dispatch.register(Operation.GRANT)
        def handle_grant(self) -> str:
            return "GRANT"

        @dispatch.register(Operation.ALTER_OWNER)
        def handle_alter_owner(self) -> str:
            return "ALTER_OWNER"

    assert FakeManagementOperation(Operation.CREATE).dispatch() == "CREATE"
    assert FakeManagementOperation(Operation.DROP).dispatch() == "DROP"
    assert FakeManagementOperation(Operation.ADD_TO_GROUP).dispatch() == "ADD_TO_GROUP"
    assert (
        FakeManagementOperation(Operation.DROP_FROM_GROUP).dispatch()
        == "DROP_FROM_GROUP"
    )
    assert FakeManagementOperation(Operation.GRANT).dispatch() == "GRANT"
    assert FakeManagementOperation(Operation.ALTER_OWNER).dispatch() == "ALTER_OWNER"


def test_user_management_operation_create_no_password():
    """CREATE user with no password raises TypeError."""
    passwordless_user = User(name="bob", is_superuser=False)
    op = UserManagementOperation(
        operation=Operation.CREATE,
        subject=passwordless_user,
    )
    with pytest.raises(TypeError):
        op.build_query()


def test_user_management_operation_alter_owner(user):
    """ALTER_OWNER builds an ALTER ... OWNER TO query."""
    db_obj = DatabaseObject(name="my_schema.my_table", type=DatabaseObjectType.TABLE)
    op = UserManagementOperation(
        operation=Operation.ALTER_OWNER,
        subject=user,
        database_object=db_obj,
    )
    result = op.build_query()
    assert "my_schema.my_table" in result
    assert "test_user_1" in result
    assert "OWNER TO" in result
    assert result.startswith("ALTER")


def test_user_management_operation_alter_owner_no_db_object(user):
    """ALTER_OWNER with no database_object raises TypeError."""
    op = UserManagementOperation(
        operation=Operation.ALTER_OWNER,
        subject=user,
    )
    with pytest.raises(TypeError):
        op.build_query()


def test_trainer_creates_new_user():
    """Trainer emits CREATE for a user present in desired but absent from current."""
    desired_user = User(
        name="new_user",
        is_superuser=False,
        password=Password(type=PasswordType.PLAIN, value="Secret123", salt=None),
    )
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
    )
    admin = trainer.train()
    create_ops = [op for op in admin.ops if op.operation is Operation.CREATE]
    assert len(create_ops) == 1
    assert create_ops[0].subject.name == "new_user"


def test_trainer_creates_new_group():
    """Trainer emits CREATE for a group present in desired but absent from current."""
    desired_group = Group(name="new_group")
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[], groups=[desired_group]),
        current_spec=Specification(users=[], groups=[]),
    )
    admin = trainer.train()
    create_ops = [op for op in admin.ops if op.operation is Operation.CREATE]
    assert len(create_ops) == 1
    assert create_ops[0].subject.name == "new_group"


def test_trainer_drops_user():
    """Trainer emits DROP for a user present in current but absent from desired."""
    current_user = User(name="old_user", is_superuser=False)
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[], groups=[]),
        current_spec=Specification(users=[current_user], groups=[]),
    )
    admin = trainer.train()
    drop_ops = [op for op in admin.ops if op.operation is Operation.DROP]
    assert len(drop_ops) == 1
    assert drop_ops[0].subject.name == "old_user"


def test_trainer_drops_group():
    """Trainer emits DROP for a group present in current but absent from desired."""
    current_group = Group(name="old_group")
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[], groups=[]),
        current_spec=Specification(users=[], groups=[current_group]),
    )
    admin = trainer.train()
    drop_ops = [op for op in admin.ops if op.operation is Operation.DROP]
    assert len(drop_ops) == 1
    assert drop_ops[0].subject.name == "old_group"


def test_trainer_add_to_group():
    """Trainer emits ADD_TO_GROUP when a user is newly assigned to a group."""
    analysts = Group(name="analysts")
    current_user = User(name="alice", is_superuser=False, member_of=None)
    desired_user = User(name="alice", is_superuser=False, member_of={"analysts"})
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[analysts]),
        current_spec=Specification(users=[current_user], groups=[]),
    )
    admin = trainer.train()
    add_ops = [op for op in admin.ops if op.operation is Operation.ADD_TO_GROUP]
    assert len(add_ops) == 1
    assert add_ops[0].subject.name == "alice"
    assert add_ops[0].group.name == "analysts"


def test_trainer_drop_from_group():
    """Trainer emits DROP_FROM_GROUP when a user is removed from a group."""
    analysts = Group(name="analysts")
    current_user = User(name="alice", is_superuser=False, member_of={"analysts"})
    desired_user = User(name="alice", is_superuser=False, member_of=set())
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[current_user], groups=[analysts]),
    )
    admin = trainer.train()
    drop_ops = [op for op in admin.ops if op.operation is Operation.DROP_FROM_GROUP]
    assert len(drop_ops) == 1
    assert drop_ops[0].subject.name == "alice"
    assert drop_ops[0].group.name == "analysts"


def test_trainer_alter_ownership():
    """Trainer emits ALTER_OWNER for every object in a user's owns list."""
    db_obj = DatabaseObject(name="my_schema.my_table", type=DatabaseObjectType.TABLE)
    desired_user = User(
        name="alice",
        is_superuser=False,
        owns=Ownerships([db_obj]),
    )
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
    )
    admin = trainer.train()
    alter_ops = [op for op in admin.ops if op.operation is Operation.ALTER_OWNER]
    assert len(alter_ops) == 1
    assert alter_ops[0].database_object == db_obj
    assert alter_ops[0].subject.name == "alice"


def test_trainer_filter_operations_suppresses_grant():
    """filter_operations returning False for GRANT suppresses all GRANT operations."""
    priv = Privilege(
        database_object=DatabaseObject(name="my_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    desired_user = User(name="alice", is_superuser=False, privileges=Privileges([priv]))
    current_user = User(name="alice", is_superuser=False, privileges=Privileges([]))
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[current_user], groups=[]),
        filter_operations=lambda op: op is Operation.REVOKE,
    )
    admin = trainer.train()
    grant_ops = [op for op in admin.ops if op.operation is Operation.GRANT]
    assert len(grant_ops) == 0


def test_prepare_subject_privileges_invalid_operation(user):
    """prepare_subject_privileges raises TypeError for non-GRANT/REVOKE operations."""
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
    )
    with pytest.raises(TypeError):
        trainer.prepare_subject_privileges(user, [], [], Operation.CREATE)


def test_trainer_filter_database_objects_excludes_grant():
    """filter_database_objects excludes GRANT ops whose object fails the filter."""
    excluded = DatabaseObject(name="secret_table", type=DatabaseObjectType.TABLE)
    excluded_priv = Privilege(database_object=excluded, action=Action.SELECT)
    allowed = DatabaseObject(name="public_table", type=DatabaseObjectType.TABLE)
    allowed_priv = Privilege(database_object=allowed, action=Action.SELECT)

    desired_user = User(
        name="alice",
        is_superuser=False,
        privileges=Privileges([excluded_priv, allowed_priv]),
    )
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
        filter_database_objects=lambda obj: obj.name != "secret_table",
    )
    admin = trainer.train()

    grant_ops = [op for op in admin.ops if op.operation is Operation.GRANT]
    granted_names = {op.privilege.database_object.name for op in grant_ops}
    assert "secret_table" not in granted_names
    assert "public_table" in granted_names


def test_trainer_filter_database_objects_excludes_alter_owner():
    """filter_database_objects excludes ALTER_OWNER ops whose object fails the filter."""
    excluded = DatabaseObject(name="secret_schema.t", type=DatabaseObjectType.TABLE)
    allowed = DatabaseObject(name="public_schema.t", type=DatabaseObjectType.TABLE)
    desired_user = User(
        name="alice",
        is_superuser=False,
        owns=Ownerships([excluded, allowed]),
    )
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
        filter_database_objects=lambda obj: obj.name != "secret_schema.t",
    )
    admin = trainer.train()

    alter_ops = [op for op in admin.ops if op.operation is Operation.ALTER_OWNER]
    owned_names = {op.database_object.name for op in alter_ops}
    assert "secret_schema.t" not in owned_names
    assert "public_schema.t" in owned_names


def test_trainer_filter_database_objects_default_allows_all():
    """The permissive default filter does not over-filter object ops."""
    table = DatabaseObject(name="a_table", type=DatabaseObjectType.TABLE)
    priv = Privilege(database_object=table, action=Action.SELECT)
    owned = DatabaseObject(name="b_schema.b_table", type=DatabaseObjectType.TABLE)
    desired_user = User(
        name="alice",
        is_superuser=False,
        privileges=Privileges([priv]),
        owns=Ownerships([owned]),
    )
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[desired_user], groups=[]),
        current_spec=Specification(users=[], groups=[]),
    )
    admin = trainer.train()

    grant_ops = [op for op in admin.ops if op.operation is Operation.GRANT]
    alter_ops = [op for op in admin.ops if op.operation is Operation.ALTER_OWNER]
    assert {op.privilege.database_object.name for op in grant_ops} == {"a_table"}
    assert {op.database_object.name for op in alter_ops} == {"b_schema.b_table"}


def test_train_includes_operation_for_truthy_non_true_filter():
    """A filter returning a truthy non-True value should include the operation.

    Regression test for issue #16: ``train`` previously gated each operation on
    ``filter_operations(...) is True``, so a callback returning a truthy
    non-``True`` value (e.g. ``1``) silently skipped the operation.
    """
    trainer = DatabaseAdministratorTrainer(
        desired_spec=Specification(users=[], groups=[]),
        current_spec=Specification(users=[], groups=[]),
        filter_operations=lambda operation: 1 if operation is Operation.CREATE else 0,
    )

    with (
        mock.patch.object(trainer, "prepare_create_subjects") as prepare_create,
        mock.patch.object(trainer, "prepare_drop_subjects") as prepare_drop,
    ):
        trainer.train()

    # CREATE filter returned 1 (truthy) -> operation must be included.
    prepare_create.assert_called_once()
    # DROP filter returned 0 (falsy) -> operation must be skipped.
    prepare_drop.assert_not_called()
