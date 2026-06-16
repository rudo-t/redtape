"""Unit tests for the specification module."""

from __future__ import annotations

import pytest

import redtape.connectors as db
from redtape.specification import (
    Action,
    DatabaseObject,
    DatabaseObjectType,
    Group,
    Ownerships,
    Password,
    PasswordType,
    Privilege,
    Privileges,
    Specification,
    User,
)


def test_read_from_yaml(spec_file):
    """Test a spec loads correctly from YAML file."""
    with open(spec_file) as yml_file:
        yml_str = yml_file.read()
    spec = Specification.from_yaml(yml_str)

    assert len(spec.users) == 1

    user = spec.users[0]

    assert user.is_superuser is True
    assert user.name == "test_user_1"
    assert user.member_of == {"my_user_group_1", "my_user_group_2"}

    password = Password(type=PasswordType.MD5, value="md5thisisnotanmd5hash", salt=None)

    assert user.password == password


def test_user_serialize_to_dict(spec_file):
    """Test serializing a User to a dictionary."""
    priv_1 = Privilege(
        database_object=DatabaseObject(name="one_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    priv_2 = Privilege(
        database_object=DatabaseObject(name="a_schema", type=DatabaseObjectType.SCHEMA),
        action=Action.CREATE,
    )
    owns_1 = DatabaseObject(
        "one_table",
        DatabaseObjectType.TABLE,
    )
    owns_2 = DatabaseObject(
        "a_schema",
        DatabaseObjectType.SCHEMA,
    )
    user = User(
        name="test_user_1",
        is_superuser=False,
        member_of={"a_user_group_1", "a_user_group_2"},
        owns=Ownerships([owns_1, owns_2]),
        password=Password(type=PasswordType.PLAIN, value="aplainpassword", salt=None),
        privileges=Privileges([priv_1, priv_2]),
    )
    expected = {
        "name": "test_user_1",
        "is_superuser": False,
        "member_of": {"a_user_group_1", "a_user_group_2"},
        "password": {
            "type": "plain",
            "value": "aplainpassword",
        },
        "owns": {
            "table": ["one_table"],
            "schema": ["a_schema"],
        },
        "privileges": {
            "table": {
                "select": [
                    "one_table",
                ],
            },
            "schema": {
                "create": [
                    "a_schema",
                ]
            },
        },
    }
    result = user.to_dict()

    assert result == expected


def test_user_deserialize_from_dict(spec_file):
    """Test deserializing a User from a dictionary."""
    priv_1 = Privilege(
        database_object=DatabaseObject(name="one_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    priv_2 = Privilege(
        database_object=DatabaseObject(name="a_schema", type=DatabaseObjectType.SCHEMA),
        action=Action.CREATE,
    )
    owns_1 = DatabaseObject(
        "one_table",
        DatabaseObjectType.TABLE,
    )
    owns_2 = DatabaseObject(
        "a_schema",
        DatabaseObjectType.SCHEMA,
    )
    expected = User(
        name="test_user_1",
        is_superuser=False,
        member_of={"a_user_group_1", "a_user_group_2"},
        owns=Ownerships([owns_1, owns_2]),
        password=Password(type=PasswordType.PLAIN, value="aplainpassword", salt=None),
        privileges=Privileges([priv_1, priv_2]),
    )
    user_dict = {
        "name": "test_user_1",
        "is_superuser": False,
        "member_of": {"a_user_group_1", "a_user_group_2"},
        "password": {
            "type": "plain",
            "value": "aplainpassword",
        },
        "owns": {
            "table": ["one_table"],
            "schema": ["a_schema"],
        },
        "privileges": {
            "table": {
                "select": [
                    "one_table",
                ],
            },
            "schema": {
                "create": [
                    "a_schema",
                ]
            },
        },
    }
    result = User.from_dict(user_dict)

    assert result == expected


@pytest.fixture
def specification(spec_file):
    with open(spec_file) as yml_file:
        yml_str = yml_file.read()
    spec = Specification.from_yaml(yml_str)
    return spec


def test_database_object_supported_actions():
    """Test is_action_supported evaluates actions correctly."""
    supported = [
        Action.SELECT,
        Action.INSERT,
        Action.UPDATE,
        Action.DROP,
        Action.REFERENCES,
        Action.SELECT_WITH_GRANT,
        Action.INSERT_WITH_GRANT,
        Action.UPDATE_WITH_GRANT,
        Action.DROP_WITH_GRANT,
        Action.REFERENCES_WITH_GRANT,
    ]
    for action in supported:
        assert DatabaseObject(
            name="test", type=DatabaseObjectType("TABLE")
        ).is_action_supported(action)

        assert DatabaseObject(
            name="test", type=DatabaseObjectType("VIEW")
        ).is_action_supported(action)

    supported = [
        Action.USAGE,
        Action.CREATE,
        Action.USAGE_WITH_GRANT,
        Action.CREATE_WITH_GRANT,
    ]
    for action in supported:
        assert DatabaseObject(
            name="test", type=DatabaseObjectType("SCHEMA")
        ).is_action_supported(action)

    supported = [
        Action.TEMPORARY,
        Action.CREATE,
        Action.TEMPORARY_WITH_GRANT,
        Action.CREATE_WITH_GRANT,
    ]
    for action in supported:
        assert DatabaseObject(
            name="test", type=DatabaseObjectType("DATABASE")
        ).is_action_supported(action)


def test_database_object_unsupported_actions():
    """Test is_action_supported evaluates actions correctly."""
    unsupported = [
        Action.USAGE,
        Action.EXECUTE,
        Action.TEMPORARY,
        Action.USAGE_WITH_GRANT,
        Action.EXECUTE_WITH_GRANT,
        Action.TEMPORARY_WITH_GRANT,
    ]
    for action in unsupported:
        assert not DatabaseObject(
            name="test", type=DatabaseObjectType("TABLE")
        ).is_action_supported(action)

        assert not DatabaseObject(
            name="test", type=DatabaseObjectType("VIEW")
        ).is_action_supported(action)

    unsupported = [
        Action.SELECT,
        Action.INSERT,
        Action.UPDATE,
        Action.DROP,
        Action.REFERENCES,
        Action.SELECT_WITH_GRANT,
        Action.INSERT_WITH_GRANT,
        Action.UPDATE_WITH_GRANT,
        Action.DROP_WITH_GRANT,
        Action.REFERENCES_WITH_GRANT,
    ]
    for action in unsupported:
        assert not DatabaseObject(
            name="test", type=DatabaseObjectType("SCHEMA")
        ).is_action_supported(action)


def test_group_serialize_to_dict(spec_file):
    """Test serializing a Group to a dictionary."""
    priv_1 = Privilege(
        database_object=DatabaseObject(
            name="one_schema", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.USAGE,
    )
    priv_2 = Privilege(
        database_object=DatabaseObject(
            name="another_schema", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.CREATE,
    )
    group = Group(
        name="test_group_1",
        privileges=Privileges([priv_1, priv_2]),
    )
    expected = {
        "name": "test_group_1",
        "privileges": {
            "schema": {
                "usage": [
                    "one_schema",
                ],
                "create": [
                    "another_schema",
                ],
            },
        },
    }
    result = group.to_dict()

    assert result == expected


def test_specification_serialize_to_dict():
    """Test serializing a Specification to a dictionary."""
    priv_1 = Privilege(
        database_object=DatabaseObject(
            name="one_schema", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.USAGE,
    )
    priv_2 = Privilege(
        database_object=DatabaseObject(
            name="another_schema", type=DatabaseObjectType.SCHEMA
        ),
        action=Action.CREATE,
    )
    group = Group(
        name="test_group_1",
        privileges=Privileges([priv_1, priv_2]),
    )
    priv_1 = Privilege(
        database_object=DatabaseObject(name="one_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    priv_2 = Privilege(
        database_object=DatabaseObject(name="a_schema", type=DatabaseObjectType.SCHEMA),
        action=Action.CREATE,
    )
    user = User(
        name="test_user_1",
        is_superuser=False,
        member_of={"a_user_group_1", "test_group_1"},
        password=Password(type=PasswordType.PLAIN, value="aplainpassword", salt=None),
        privileges=Privileges([priv_1, priv_2]),
    )

    specification = Specification(users=[user], groups=[group])

    expected = {
        "users": [
            {
                "name": "test_user_1",
                "is_superuser": False,
                "member_of": {"a_user_group_1", "test_group_1"},
                "password": {
                    "type": "plain",
                    "value": "aplainpassword",
                },
                "privileges": {
                    "table": {
                        "select": [
                            "one_table",
                        ],
                    },
                    "schema": {
                        "create": [
                            "a_schema",
                        ]
                    },
                },
            }
        ],
        "groups": [
            {
                "name": "test_group_1",
                "privileges": {
                    "schema": {
                        "usage": [
                            "one_schema",
                        ],
                        "create": [
                            "another_schema",
                        ],
                    },
                },
            },
        ],
    }

    result = specification.to_dict()

    assert result == expected


class FakeRedshiftConnector:
    """A fake RedshiftConnector for testing."""

    def iter_tables(self):
        """Iterate over fake tables."""
        tables = [
            db.Table(
                database_name="prod",
                schema_name="public",
                table_name="users",
                table_owner="prod_admin",
                table_type="TABLE",
                table_acl="prod_admin=arwdRxtD/prod_admin,group prod_analytics=r/prod_admin",
                remarks=None,
            ),
            db.Table(
                database_name="prod",
                schema_name="public",
                table_name="sales",
                table_owner="prod_admin",
                table_type="TABLE",
                table_acl="prod_admin=arwdRxtD/prod_admin,group prod_analytics=r/prod_admin",
                remarks=None,
            ),
            db.Table(
                database_name="prod",
                schema_name="analytics",
                table_name="sales_per_user",
                table_owner="prod_analyst",
                table_type="VIEW",
                table_acl="prod_analyst=arwdRxtD/prod_admin,group analytics_consumers=r/prod_analyst",
                remarks=None,
            ),
            db.Table(
                database_name="dev",
                schema_name="dev_analytics",
                table_name="dev_table_1",
                table_owner="dev_analyst",
                table_type="TABLE",
                table_acl="dev_analyst=arwdRxtD/prod_admin",
                remarks=None,
            ),
            db.Table(
                database_name="dev",
                schema_name="dev_analytics",
                table_name="dev_table_2",
                table_owner="dev_analyst",
                table_type="TABLE",
                table_acl="dev_analyst=arwdRxtD/prod_admin",
                remarks=None,
            ),
        ]
        for table in tables:
            yield table

    def iter_schemas(self):
        """Iterate over fake schemas."""
        schemas = [
            db.Schema(
                database_name="prod",
                schema_name="public",
                schema_owner="prod_admin",
                schema_type="local",
                schema_acl="{prod_admin=UC/prod_admin,group prod_analytics=U/prod_admin}",
                source_database=None,
                schema_option=None,
            ),
            db.Schema(
                database_name="prod",
                schema_name="analytics",
                schema_owner="prod_analyst",
                schema_type="local",
                schema_acl="{prod_analyst=UC/prod_admin,group prod_analytics=UC/prod_admin}",
                source_database=None,
                schema_option=None,
            ),
            db.Schema(
                database_name="dev",
                schema_name="dev_analytics",
                schema_owner="dev_analyst",
                schema_type="local",
                schema_acl="{dev_analyst=UC/dev_analyst}",
                source_database=None,
                schema_option=None,
            ),
        ]
        for schema in schemas:
            yield schema

    def iter_databases(self):
        """Iterate over fake databases."""
        databases = [
            db.Database(
                database_name="prod",
                database_owner="prod_admin",
                database_acl="{prod_admin=CT/prod_admin,prod_analyst=T/prod_admin}",
            ),
            db.Database(
                database_name="dev",
                database_owner="dev_analyst",
                database_acl="{dev_analyst=CT/prod_admin}",
            ),
        ]
        for database in databases:
            yield database

    def iter_users(self):
        """Iterate over fake users."""
        users = [
            db.User(
                usename="prod_admin",
                usesysid=100,
                usecreatedb=True,
                usesuper=True,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
            db.User(
                usename="prod_analyst",
                usesysid=101,
                usecreatedb=False,
                usesuper=False,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
            db.User(
                usename="dev_analyst",
                usesysid=102,
                usecreatedb=False,
                usesuper=False,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
        ]

        for user in users:
            yield user

    def iter_groups(self):
        """Iterate over fake groups."""
        groups = [
            db.Group(
                groname="prod_analytics",
                grosysid=103,
                grolist=[101],
            ),
            db.Group(
                groname="consumer_analytics",
                grosysid=104,
                grolist=[102],
            ),
            db.Group(
                groname="everyone",
                grosysid=105,
                grolist=[100, 101, 102],
            ),
        ]

        for group in groups:
            yield group


def test_specification_from_redshift_connector_users_created():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    assert len(spec.users) == 3

    users = set((user.name for user in spec.users))
    assert users == {"dev_analyst", "prod_analyst", "prod_admin"}

    superusers = [user for user in spec.users if user.is_superuser is True]
    assert len(superusers) == 1
    assert superusers[0].name == "prod_admin"


def test_specification_from_redshift_connector_user_memberships():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    for user in spec.users:
        assert user.member_of is not None and len(user.member_of) >= 1
        assert "everyone" in user.member_of, f"{user} is not part of 'everyone' group"

        if user.name == "prod_admin":
            assert len(user.member_of) == 1

        elif user.name == "prod_analyst":
            assert len(user.member_of) == 2
            assert "prod_analytics" in user.member_of

        elif user.name == "dev_analyst":
            assert len(user.member_of) == 2
            assert "consumer_analytics" in user.member_of

    assert len(spec.groups) == 3

    groups = set((group.name for group in spec.groups))
    assert groups == {"prod_analytics", "consumer_analytics", "everyone"}


def test_specification_from_redshift_connector_user_ownerships():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    for user in spec.users:
        if user.name == "prod_admin":
            should_own = (
                DatabaseObject("prod.public.users", DatabaseObjectType.TABLE),
                DatabaseObject("prod.public.sales", DatabaseObjectType.TABLE),
                DatabaseObject("prod.public", DatabaseObjectType.SCHEMA),
                DatabaseObject("prod", DatabaseObjectType.DATABASE),
            )
            assert user.owns == Ownerships(should_own)

        elif user.name == "prod_analyst":
            should_own = (
                DatabaseObject(
                    "prod.analytics.sales_per_user", DatabaseObjectType.VIEW
                ),
                DatabaseObject("prod.analytics", DatabaseObjectType.SCHEMA),
            )
            assert user.owns == Ownerships(should_own)

        elif user.name == "dev_analyst":
            should_own = (
                DatabaseObject(
                    "dev.dev_analytics.dev_table_1", DatabaseObjectType.TABLE
                ),
                DatabaseObject(
                    "dev.dev_analytics.dev_table_2", DatabaseObjectType.TABLE
                ),
                DatabaseObject("dev.dev_analytics", DatabaseObjectType.SCHEMA),
                DatabaseObject("dev", DatabaseObjectType.DATABASE),
            )
            assert user.owns == Ownerships(should_own)


def test_specification_from_redshift_connector_user_privileges():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    all_table_actions = [Action(c) for c in "arwdxD"]
    all_schema_actions = [Action(c) for c in "UC"]
    all_database_actions = [Action(c) for c in "CT"]

    for user in spec.users:
        if user.name == "prod_admin":
            should_have = []

            for table in ("prod.public.users", "prod.public.sales"):
                for action in all_table_actions:
                    priv = Privilege(
                        DatabaseObject(table, DatabaseObjectType.TABLE), action
                    )
                    should_have.append(priv)

            for action in all_schema_actions:
                priv = Privilege(
                    DatabaseObject("prod.public", DatabaseObjectType.SCHEMA), action
                )
                should_have.append(priv)

            for action in all_database_actions:
                priv = Privilege(
                    DatabaseObject("prod", DatabaseObjectType.DATABASE), action
                )
                should_have.append(priv)

            assert user.privileges == Privileges(should_have)

        elif user.name == "prod_analyst":
            should_have = []

            for action in all_table_actions:
                priv = Privilege(
                    DatabaseObject(
                        "prod.analytics.sales_per_user", DatabaseObjectType.VIEW
                    ),
                    action,
                )
                should_have.append(priv)

            for action in all_schema_actions:
                priv = Privilege(
                    DatabaseObject("prod.analytics", DatabaseObjectType.SCHEMA), action
                )
                should_have.append(priv)

            priv = Privilege(
                DatabaseObject("prod", DatabaseObjectType.DATABASE), Action("T")
            )
            should_have.append(priv)

            assert user.privileges == Privileges(should_have)

        elif user.name == "dev_analyst":
            should_have = []

            for table in (
                "dev.dev_analytics.dev_table_1",
                "dev.dev_analytics.dev_table_2",
            ):
                for action in all_table_actions:
                    priv = Privilege(
                        DatabaseObject(table, DatabaseObjectType.TABLE), action
                    )
                    should_have.append(priv)

            for action in all_schema_actions:
                priv = Privilege(
                    DatabaseObject("dev.dev_analytics", DatabaseObjectType.SCHEMA),
                    action,
                )
                should_have.append(priv)

            for action in all_database_actions:
                priv = Privilege(
                    DatabaseObject("dev", DatabaseObjectType.DATABASE), action
                )
                should_have.append(priv)

            assert user.privileges == Privileges(should_have)


def test_specification_from_redshift_connector_groups_created():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    assert len(spec.groups) == 3

    groups = set((group.name for group in spec.groups))
    assert groups == {"prod_analytics", "consumer_analytics", "everyone"}


def test_database_object_from_parts_one_arg():
    """from_parts with one arg builds a single-segment name."""
    db_obj = DatabaseObject.from_parts("mydb", type=DatabaseObjectType.DATABASE)
    assert db_obj.name == "mydb"
    assert db_obj._type == DatabaseObjectType.DATABASE


def test_database_object_from_parts_two_args():
    """from_parts with two args joins them with a dot."""
    db_obj = DatabaseObject.from_parts("mydb", "my_schema", type=DatabaseObjectType.SCHEMA)
    assert db_obj.name == "mydb.my_schema"
    assert db_obj._type == DatabaseObjectType.SCHEMA


def test_database_object_from_parts_three_args():
    """from_parts with three args builds a fully-qualified name."""
    db_obj = DatabaseObject.from_parts("mydb", "my_schema", "my_table", type=DatabaseObjectType.TABLE)
    assert db_obj.name == "mydb.my_schema.my_table"
    assert db_obj._type == DatabaseObjectType.TABLE


def test_database_object_parts_one_level():
    """parts returns (db, None, None) for a single-segment name."""
    db_obj = DatabaseObject(name="mydb", type=DatabaseObjectType.DATABASE)
    db_part, schema_part, obj_part = db_obj.parts
    assert db_part == DatabaseObject("mydb", DatabaseObjectType.DATABASE)
    assert schema_part is None
    assert obj_part is None


def test_database_object_parts_two_levels():
    """parts returns (db, schema, None) for a two-segment name."""
    db_obj = DatabaseObject(name="mydb.my_schema", type=DatabaseObjectType.SCHEMA)
    db_part, schema_part, obj_part = db_obj.parts
    assert db_part == DatabaseObject("mydb", DatabaseObjectType.DATABASE)
    assert schema_part == DatabaseObject("my_schema", DatabaseObjectType.SCHEMA)
    assert obj_part is None


def test_database_object_parts_three_levels():
    """parts returns (db, schema, table) for a three-segment name."""
    db_obj = DatabaseObject(name="mydb.my_schema.my_table", type=DatabaseObjectType.TABLE)
    db_part, schema_part, obj_part = db_obj.parts
    assert db_part == DatabaseObject("mydb", DatabaseObjectType.DATABASE)
    assert schema_part == DatabaseObject("my_schema", DatabaseObjectType.SCHEMA)
    assert obj_part == DatabaseObject("my_table", DatabaseObjectType.TABLE)


def test_database_object_is_wildcard():
    """is_wildcard returns True only for the bare '*' name."""
    assert DatabaseObject(name="*", type=DatabaseObjectType.TABLE).is_wildcard() is True
    assert DatabaseObject(name="my_table", type=DatabaseObjectType.TABLE).is_wildcard() is False


def test_database_object_has_wildcard_part():
    """has_wildcard_part detects wildcards at the correct segment level."""
    table_wildcard = DatabaseObject(name="mydb.my_schema.*", type=DatabaseObjectType.TABLE)
    assert table_wildcard.has_wildcard_part(DatabaseObjectType.TABLE) is True
    assert table_wildcard.has_wildcard_part(DatabaseObjectType.SCHEMA) is False
    assert table_wildcard.has_wildcard_part(DatabaseObjectType.DATABASE) is False

    schema_wildcard = DatabaseObject(name="mydb.*", type=DatabaseObjectType.SCHEMA)
    assert schema_wildcard.has_wildcard_part(DatabaseObjectType.SCHEMA) is True
    assert schema_wildcard.has_wildcard_part(DatabaseObjectType.DATABASE) is False


def test_privilege_validate_supported_action():
    """validate returns (True, None) when the action is supported by the object type."""
    priv = Privilege(
        database_object=DatabaseObject(name="my_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    success, failures = priv.validate()
    assert success is True
    assert failures is None


def test_privilege_validate_unsupported_action():
    """validate returns (False, [failure]) when the action is not supported."""
    priv = Privilege(
        database_object=DatabaseObject(name="my_db", type=DatabaseObjectType.DATABASE),
        action=Action.SELECT,
    )
    success, failures = priv.validate()
    assert success is False
    assert failures is not None and len(failures) == 1


def test_password_str_plain():
    pw = Password(type=PasswordType.PLAIN, value="MySecret1", salt=None)
    assert str(pw) == "MySecret1"


def test_password_str_md5():
    pw = Password(type=PasswordType.MD5, value="abc123hash", salt=None)
    assert str(pw) == "md5abc123hash"


def test_password_str_sha256():
    pw = Password(type=PasswordType.SHA256, value="deadbeef", salt=None)
    assert str(pw) == "sha256|deadbeef"


def test_password_str_disabled():
    pw = Password(type=PasswordType.DISABLED)
    assert str(pw) == "DISABLED"


def test_password_validate_valid():
    pw = Password(type=PasswordType.PLAIN, value="Secret123", salt=None)
    success, failures = pw.validate()
    assert success is True
    assert failures is None


def test_password_validate_too_short():
    """PLAIN password shorter than 8 chars fails validation."""
    pw = Password(type=PasswordType.PLAIN, value="Sh0rt", salt=None)
    success, failures = pw.validate()
    assert success is False
    assert failures is not None


def test_password_validate_no_uppercase():
    """PLAIN password with no uppercase char fails validation."""
    pw = Password(type=PasswordType.PLAIN, value="secret1234", salt=None)
    success, failures = pw.validate()
    assert success is False
    assert any("uppercase" in f.message for f in failures)


def test_password_validate_no_lowercase():
    """PLAIN password with no lowercase char fails validation."""
    pw = Password(type=PasswordType.PLAIN, value="SECRET1234", salt=None)
    success, failures = pw.validate()
    assert success is False
    assert any("lowercase" in f.message for f in failures)


def test_password_validate_no_digit():
    """PLAIN password with no digit fails validation."""
    pw = Password(type=PasswordType.PLAIN, value="Secretsecret", salt=None)
    success, failures = pw.validate()
    assert success is False
    assert any("digit" in f.message for f in failures)


def test_user_add_privilege_creates_set():
    """add_privilege creates a Privileges set when privileges is None."""
    user = User(name="alice", is_superuser=False)
    priv = Privilege(
        database_object=DatabaseObject(name="my_table", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    assert user.privileges is None
    user.add_privilege(priv)
    assert user.privileges == Privileges([priv])


def test_user_add_privilege_extends_existing():
    """add_privilege appends to an existing Privileges set."""
    priv1 = Privilege(
        database_object=DatabaseObject(name="table_a", type=DatabaseObjectType.TABLE),
        action=Action.SELECT,
    )
    priv2 = Privilege(
        database_object=DatabaseObject(name="table_b", type=DatabaseObjectType.TABLE),
        action=Action.INSERT,
    )
    user = User(name="alice", is_superuser=False, privileges=Privileges([priv1]))
    user.add_privilege(priv2)
    assert user.privileges == Privileges([priv1, priv2])


def test_user_add_owned_db_object():
    """add_owned_db_object creates Ownerships when owns is None, then extends it."""
    user = User(name="alice", is_superuser=False)
    db_obj = DatabaseObject(name="my_table", type=DatabaseObjectType.TABLE)
    assert user.owns is None
    user.add_owned_db_object(db_obj)
    assert user.owns == Ownerships([db_obj])
    db_obj2 = DatabaseObject(name="my_schema", type=DatabaseObjectType.SCHEMA)
    user.add_owned_db_object(db_obj2)
    assert db_obj2 in user.owns


def test_user_validate_invalid_privilege():
    """User.validate propagates privilege validation failures."""
    priv = Privilege(
        database_object=DatabaseObject(name="my_db", type=DatabaseObjectType.DATABASE),
        action=Action.SELECT,
    )
    user = User(name="alice", is_superuser=False, privileges=Privileges([priv]))
    success, failures = user.validate()
    assert success is False
    assert failures is not None and len(failures) == 1


def test_user_validate_invalid_password():
    """User.validate propagates password validation failures."""
    pw = Password(type=PasswordType.PLAIN, value="weak", salt=None)
    user = User(name="alice", is_superuser=False, privileges=Privileges([]), password=pw)
    success, failures = user.validate()
    assert success is False
    assert failures is not None


def test_group_add_privilege_creates_set():
    """Group.add_privilege creates a Privileges set when privileges is None."""
    group = Group(name="analysts")
    priv = Privilege(
        database_object=DatabaseObject(name="my_schema", type=DatabaseObjectType.SCHEMA),
        action=Action.USAGE,
    )
    assert group.privileges is None
    group.add_privilege(priv)
    assert group.privileges == Privileges([priv])


def test_group_validate_invalid_privilege():
    """Group.validate propagates privilege validation failures."""
    priv = Privilege(
        database_object=DatabaseObject(name="my_db", type=DatabaseObjectType.DATABASE),
        action=Action.SELECT,
    )
    group = Group(name="analysts", privileges=Privileges([priv]))
    success, failures = group.validate()
    assert success is False
    assert failures is not None and len(failures) == 1


def test_specification_from_yaml_file(spec_file):
    """Specification.from_yaml_file loads from a path object."""
    spec = Specification.from_yaml_file(spec_file)
    assert len(spec.users) == 1
    assert spec.users[0].name == "test_user_1"


def test_specification_roundtrip_yaml():
    """A Specification serialised to YAML and back is equivalent."""
    user = User(name="alice", is_superuser=False)
    spec = Specification(users=[user], groups=[])
    restored = Specification.from_yaml(spec.to_yaml())
    assert len(restored.users) == 1
    assert restored.users[0].name == "alice"


def test_specification_roundtrip_json():
    """A Specification serialised to JSON and back is equivalent."""
    user = User(name="alice", is_superuser=False)
    spec = Specification(users=[user], groups=[])
    restored = Specification.from_json(spec.to_json())
    assert len(restored.users) == 1
    assert restored.users[0].name == "alice"


def test_specification_validate_user_in_missing_group():
    """validate fails when a user references a group not declared in the spec."""
    user = User(name="alice", is_superuser=False, member_of={"ghost_group"})
    spec = Specification(users=[user], groups=[])
    success, failures = spec.validate()
    assert success is False
    assert failures is not None and len(failures) >= 1


def test_specification_schema_names_not_in_yaml():
    """schema_names is an internal field and must not appear in YAML output."""
    spec = Specification(users=[], groups=[], schema_names={"mydb": ["public"]})
    assert "schema_names" not in spec.to_yaml()
    assert "schema_names" not in spec.to_dict()


def test_specification_schema_names_from_connector():
    """from_redshift_connector populates schema_names from Schema entities."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)
    assert "prod" in spec.schema_names
    assert set(spec.schema_names["prod"]) == {"public", "analytics"}
    assert "dev" in spec.schema_names
    assert spec.schema_names["dev"] == ["dev_analytics"]


def test_specification_from_redshift_connector_groups_privileges():
    """Test loading an specification from a RedshiftConnector."""
    connector = FakeRedshiftConnector()
    spec = Specification.from_redshift_connector(connector)

    for group in spec.groups:
        if group.name == "prod_analytics":
            should_have = []

            for table in ("prod.public.users", "prod.public.sales"):
                priv = Privilege(
                    DatabaseObject(table, DatabaseObjectType.TABLE), Action("r")
                )
                should_have.append(priv)

            priv_1 = Privilege(
                DatabaseObject("prod.public", DatabaseObjectType.SCHEMA), Action("U")
            )
            priv_2 = Privilege(
                DatabaseObject("prod.analytics", DatabaseObjectType.SCHEMA), Action("U")
            )
            priv_3 = Privilege(
                DatabaseObject("prod.analytics", DatabaseObjectType.SCHEMA), Action("C")
            )
            should_have.extend([priv_1, priv_2, priv_3])

            assert group.privileges == Privileges(should_have)

        elif group.name == "analytics_consumer":
            should_have = []
            priv = Privilege(
                DatabaseObject(
                    "prod.analytics.sales_per_user", DatabaseObjectType.VIEW
                ),
                Action("r"),
            )
            should_have.append(priv)

            assert group.privileges == Privileges(should_have)

        elif group.name == "everyone":
            assert group.privileges is None
