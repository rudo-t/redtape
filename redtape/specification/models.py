"""Specification models.

This module contains all specification models to be loaded from a specification
file or a database connector. The core of Redtape is essentially deserializing
both the specification file and the current specification as given by a
database connector into the same models. This way, they may be compared to
prepare the queries that need to be run."""

from __future__ import annotations

import contextlib
import itertools
import operator
import re
from collections.abc import Iterator
from enum import Enum

import attrs

from redtape.connectors import Database, RedshiftConnector, Schema, Table

# A conservative pattern for a single, unqualified Redshift/Postgres
# identifier: must start with a letter or underscore, followed by letters,
# digits, or underscores. This is deliberately stricter than what Redshift
# actually allows (quoted identifiers can contain almost anything) -- it's
# meant as defense in depth against spec-supplied names carrying characters
# with special meaning in SQL (quotes, semicolons, comment markers, etc.),
# on top of the identifier-quoting done when building queries (see
# redtape/admin.py).
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier_name(name: str) -> bool:
    """Return True if name is safe to use as a single SQL identifier."""
    return bool(_IDENTIFIER_RE.match(name))


def is_valid_database_object_name(name: str) -> bool:
    """Return True if name is safe as a (possibly dot-qualified, possibly
    wildcarded) database object identifier, e.g. ``db.schema.table`` or
    ``db.schema.*``."""
    parts = name.split(".")
    return len(parts) > 0 and all(
        part == "*" or is_valid_identifier_name(part) for part in parts
    )


class Action(Enum):
    SELECT = "r"
    INSERT = "a"
    UPDATE = "w"
    DELETE = "d"
    DROP = "D"
    REFERENCES = "x"
    CREATE = "C"
    USAGE = "U"
    EXECUTE = "X"
    TEMPORARY = "T"
    RULE = "R"
    TRIGGER = "t"
    CONNECT = "c"

    SELECT_WITH_GRANT = "r*"
    INSERT_WITH_GRANT = "a*"
    UPDATE_WITH_GRANT = "w*"
    DELETE_WITH_GRANT = "d*"
    DROP_WITH_GRANT = "D*"
    REFERENCES_WITH_GRANT = "x*"
    CREATE_WITH_GRANT = "C*"
    USAGE_WITH_GRANT = "U*"
    EXECUTE_WITH_GRANT = "X*"
    TEMPORARY_WITH_GRANT = "T*"
    RULE_WITH_GRANT = "R*"
    TRIGGER_WITH_GRANT = "t*"
    CONNECT_WITH_GRANT = "c*"


class DatabaseObjectType(Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    FUNCTION = "FUNCTION"
    SCHEMA = "SCHEMA"
    DATABASE = "DATABASE"
    LANGUAGE = "LANGUAGE"
    PROCEDURE = "PROCEDURE"

    @property
    def supported_actions(self) -> set[Action]:
        if self in (DatabaseObjectType.TABLE, DatabaseObjectType.VIEW):
            supported = {
                Action.SELECT,
                Action.INSERT,
                Action.UPDATE,
                Action.DROP,
                Action.DELETE,
                Action.REFERENCES,
                Action.CREATE_WITH_GRANT,
                Action.SELECT_WITH_GRANT,
                Action.INSERT_WITH_GRANT,
                Action.UPDATE_WITH_GRANT,
                Action.DROP_WITH_GRANT,
                Action.DELETE_WITH_GRANT,
                Action.REFERENCES_WITH_GRANT,
            }
        elif self is DatabaseObjectType.DATABASE:
            supported = {
                Action.CREATE,
                Action.TEMPORARY,
                Action.CONNECT,
                Action.CREATE_WITH_GRANT,
                Action.TEMPORARY_WITH_GRANT,
                Action.CONNECT_WITH_GRANT,
            }
        elif self is DatabaseObjectType.SCHEMA:
            supported = {
                Action.CREATE,
                Action.USAGE,
                Action.CREATE_WITH_GRANT,
                Action.USAGE_WITH_GRANT,
            }
        elif self in (DatabaseObjectType.FUNCTION, DatabaseObjectType.PROCEDURE):
            supported = {
                Action.EXECUTE,
                Action.EXECUTE_WITH_GRANT,
            }
        elif self is DatabaseObjectType.LANGUAGE:
            supported = {
                Action.USAGE,
                Action.USAGE_WITH_GRANT,
            }
        return supported


class UnsupportedPrivilegeError(ValueError):
    """A spec references a privilege that read/write shorthand cannot express."""


_READ = "read"
_WRITE = "write"

# `read`/`write` is the only privilege syntax a redtape spec accepts, for
# users and groups today and future object types alike. Kept as a plain
# str-keyed table -- rather than baked into the YAML loader -- so that
# future model can reuse expand_action_shorthand() without a second
# parser. A missing (shorthand, object_type) entry means that combination is
# not expressible in a spec (e.g. `write` on DATABASE).
_SHORTHAND_EXPANSION: dict[str, dict[DatabaseObjectType, frozenset[Action]]] = {
    _READ: {
        DatabaseObjectType.TABLE: frozenset({Action.SELECT}),
        DatabaseObjectType.VIEW: frozenset({Action.SELECT}),
        DatabaseObjectType.SCHEMA: frozenset({Action.USAGE}),
        DatabaseObjectType.DATABASE: frozenset({Action.CONNECT}),
    },
    _WRITE: {
        DatabaseObjectType.TABLE: frozenset(
            {Action.SELECT, Action.INSERT, Action.UPDATE, Action.DELETE}
        ),
        DatabaseObjectType.SCHEMA: frozenset({Action.USAGE, Action.CREATE}),
    },
}

# FUNCTION/PROCEDURE/LANGUAGE have no read/write mapping at all: they're
# called out separately from a missing (shorthand, object_type) entry so the
# error message can say so plainly, rather than complaining about one
# specific shorthand at a time.
_OBJECT_TYPES_WITHOUT_SHORTHAND = frozenset(
    {
        DatabaseObjectType.FUNCTION,
        DatabaseObjectType.PROCEDURE,
        DatabaseObjectType.LANGUAGE,
    }
)


def expand_action_shorthand(
    shorthand: str, object_type: DatabaseObjectType
) -> frozenset[Action]:
    """Expand a `read`/`write` privilege shorthand into concrete Actions.

    Raises:
        UnsupportedPrivilegeError: if `shorthand` is not `read`/`write` (e.g.
            a raw action name like `select`), if `object_type` has no
            read/write mapping at all (FUNCTION, PROCEDURE, LANGUAGE), or if
            this shorthand has no mapping for this object type (e.g. `write`
            on DATABASE).
    """
    normalized = shorthand.lower()

    if normalized not in _SHORTHAND_EXPANSION:
        raise UnsupportedPrivilegeError(
            f"{shorthand!r} is not a supported privilege. Redtape specs only "
            "accept 'read'/'write' shorthand for privileges; raw action "
            "names (e.g. 'select', 'insert', 'drop') are no longer accepted."
        )

    if object_type in _OBJECT_TYPES_WITHOUT_SHORTHAND:
        raise UnsupportedPrivilegeError(
            f"{object_type.value} privileges have no read/write mapping and "
            "can no longer be expressed in a redtape spec."
        )

    try:
        return _SHORTHAND_EXPANSION[normalized][object_type]
    except KeyError:
        raise UnsupportedPrivilegeError(
            f"{normalized!r} has no privilege mapping for {object_type.value} "
            "and cannot be expressed in a redtape spec."
        ) from None


@attrs.frozen(hash=True, slots=True)
class DatabaseObject:
    name: str
    _type: DatabaseObjectType

    def is_action_supported(self, action: Action) -> bool:
        """Check if an Action is supported by this DatabaseObject."""
        return action in self._type.supported_actions

    @classmethod
    def from_parts(cls, *args, type: DatabaseObjectType):
        name = ".".join(args)
        return cls(name, type)

    @property
    def parts(
        self,
    ) -> tuple[DatabaseObject | None, DatabaseObject | None, DatabaseObject | None]:
        """Split this object into individual DatabaseObject, if possible.

        A DatabaseObject can be split if it's name contains '.', for example:

        >>> my_obj = DatabaseObject(name="mydb.my_schema", type=DatabaseObjectType.SCHEMA)
        >>> db_obj, schema_obj, _ = my_obj.parts()
        >>> print(db_obj)
        <DatabaseObjectType.DATABASE: "mydb">
        >>> print(schema_obj)
        <DatabaseObjectType.SCHEMA: "my_schema">
        """
        parts = self.name.split(".")
        obj = DatabaseObject(
            name=parts.pop(-1),
            type=self._type,
        )
        db_obj = None
        schema_obj = None

        if len(parts) == 2:
            database, schema = parts
            db_obj = DatabaseObject(
                name=database,
                type=DatabaseObjectType.DATABASE,
            )
            schema_obj = DatabaseObject(
                name=schema,
                type=DatabaseObjectType.SCHEMA,
            )
        elif len(parts) == 1:
            (database,) = parts
            db_obj = DatabaseObject(
                name=database,
                type=DatabaseObjectType.DATABASE,
            )
            schema_obj = obj
            obj = None
        else:
            db_obj = obj
            obj = None

        return (db_obj, schema_obj, obj)

    def is_wildcard(self) -> bool:
        """Return True if this object is a wildcard."""
        return self.name == "*"

    def has_wildcard_part(self, _type: DatabaseObjectType) -> bool:
        """Return True if this object has a wildcard on a given part.

        The part is determined by the DatabaseObjectType passed. For example:
        >>> my_obj = DatabaseObject(name="mydb.my_schema.*", type=DatabaseObjectType.TABLE)
        >>> my_obj.has_wildcard_part(DatabaseObjectType.TABLE)
        True
        >>> my_obj.has_wildcard_part(DatabaseObjectType.SCHEMA)
        False
        """
        return any(
            p
            for p in self.parts
            if p is not None and p._type == _type and p.is_wildcard()
        )

    def __str__(self):
        return f"<{self._type}: {self.name}>"


@attrs.frozen(hash=True, slots=True)
class Privilege:
    database_object: DatabaseObject
    action: Action | None = None

    def validate(self) -> tuple[bool, list[ValidationFailure] | None]:
        failures: list[ValidationFailure] = []

        if not is_valid_database_object_name(self.database_object.name):
            failures.append(
                ValidationFailure(
                    subject=self.database_object,
                    message=(
                        f"{self.database_object.name!r} is not a valid Redshift "
                        "identifier."
                    ),
                )
            )

        if self.action is not None and not self.database_object.is_action_supported(
            self.action
        ):
            failures.append(
                ValidationFailure(
                    subject=self.database_object,
                    message=f"{self.action} cannot be granted to {self.database_object}",
                )
            )

        if len(failures) == 0:
            return True, None
        return False, failures


class Operation(Enum):
    CREATE = "CREATE"
    DROP = "DROP"
    DROP_FROM_GROUP = "DROP_FROM_GROUP"
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    ADD_TO_GROUP = "ADD_TO_GROUP"
    ALTER_OWNER = "ALTER_OWNER"

    @property
    def canonical(self) -> str:
        if self is Operation.DROP_FROM_GROUP:
            return "DROP"
        elif self is Operation.ADD_TO_GROUP:
            return "ADD"
        elif self is Operation.ALTER_OWNER:
            return "ALTER"
        else:
            return self.value


@attrs.frozen(hash=True)
class ValidationFailure:
    subject: DatabaseObject | User | Group | Role
    message: str


class Privileges(set):
    """A set of privileges.

    Needed only to support custom serialization/deserialization.
    """


class Ownerships(set):
    """A set of DatabaseObjects owned.

    Needed only to support custom serialization/deserialization.
    """


@attrs.define(slots=True)
class Group:
    name: str
    privileges: Privileges | None = None

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, Group):
            return (self.name, self.privileges) == (other.name, other.privileges)
        else:
            return NotImplemented

    def __repr__(self):
        return f"Group(name={self.name}, privileges={self.privileges})"

    def add_privilege(self, privilege: Privilege):
        try:
            self.privileges.add(privilege)
        except AttributeError:
            self.privileges = Privileges((privilege,))

    def validate(self) -> tuple[bool, list[ValidationFailure] | None]:
        validation_failures: list[ValidationFailure] = []
        success = True

        if not is_valid_identifier_name(self.name):
            validation_failures.append(
                ValidationFailure(
                    subject=self,
                    message=f"{self.name!r} is not a valid Redshift identifier.",
                )
            )
            success = False

        if self.privileges is not None:
            for privilege in self.privileges:
                _, failures = privilege.validate()

                if failures is not None:
                    validation_failures.extend(failures)
                    success = False

        if success is True:
            return success, None
        return success, validation_failures


@attrs.define(slots=True)
class Role:
    """A Redshift RBAC Role, which may itself be a member of other Roles.

    Attributes:
        name (str): The role name.
        member_of (list[str]): A list of role names this role is a member of
            (role-to-role inheritance).
        privileges (Privileges): A set of Privileges associated with this role.
    """

    name: str
    member_of: set[str] | None = None
    privileges: Privileges | None = None

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, Role):
            return (self.name, self.member_of, self.privileges) == (
                other.name,
                other.member_of,
                other.privileges,
            )
        else:
            return NotImplemented

    def __repr__(self):
        return (
            f"Role(name={self.name}, member_of={self.member_of}, "
            f"privileges={self.privileges})"
        )

    def add_privilege(self, privilege: Privilege):
        try:
            self.privileges.add(privilege)
        except AttributeError:
            self.privileges = Privileges((privilege,))

    def validate(self) -> tuple[bool, list[ValidationFailure] | None]:
        validation_failures: list[ValidationFailure] = []
        success = True

        if not is_valid_identifier_name(self.name):
            validation_failures.append(
                ValidationFailure(
                    subject=self,
                    message=f"{self.name!r} is not a valid Redshift identifier.",
                )
            )
            success = False

        if self.privileges is not None:
            for privilege in self.privileges:
                _, failures = privilege.validate()

                if failures is not None:
                    validation_failures.extend(failures)
                    success = False

        if success is True:
            return success, None
        return success, validation_failures


@attrs.define(slots=True)
class User:
    """A User in a database who can be a subject of privileges.

    Attributes:
        name (str): The user name.
        is_superuser (bool): Whether the user is a superuser or not.
        groups (list[str]): A list of group names the user is a member of.
        roles (list[str]): A list of role names the user is a member of.
        privileges (Privileges): A set of Privileges associated with this user.
    """

    name: str
    is_superuser: bool
    groups: set[str] | None = None
    roles: set[str] | None = None
    privileges: Privileges | None = None
    owns: Ownerships | None = None

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, User):
            return (
                self.name,
                self.privileges,
                self.is_superuser,
                self.groups,
                self.roles,
            ) == (
                other.name,
                other.privileges,
                other.is_superuser,
                other.groups,
                other.roles,
            )
        else:
            return NotImplemented

    def __repr__(self):
        return f"User(name={self.name}, privileges={self.privileges})"

    def add_privilege(self, privilege: Privilege):
        try:
            self.privileges.add(privilege)
        except AttributeError:
            self.privileges = Privileges((privilege,))

    def add_owned_db_object(self, db_obj: DatabaseObject):
        try:
            self.owns.add(db_obj)
        except AttributeError:
            self.owns = Ownerships((db_obj,))

    def validate(self) -> tuple[bool, list[ValidationFailure] | None]:
        validation_failures: list[ValidationFailure] = []
        success = True

        if not is_valid_identifier_name(self.name):
            validation_failures.append(
                ValidationFailure(
                    subject=self,
                    message=f"{self.name!r} is not a valid Redshift identifier.",
                )
            )
            success = False

        if self.privileges is not None:
            for privilege in self.privileges:
                _, failures = privilege.validate()

                if failures is not None:
                    validation_failures.extend(failures)
                    success = False

        if self.owns is not None:
            for db_obj in self.owns:
                if not is_valid_database_object_name(db_obj.name):
                    validation_failures.append(
                        ValidationFailure(
                            subject=db_obj,
                            message=(
                                f"{db_obj.name!r} is not a valid Redshift identifier."
                            ),
                        )
                    )
                    success = False

        if success is True:
            return success, None
        return success, validation_failures


@attrs.define(slots=True)
class Specification:
    users: list[User] | None = None
    groups: list[Group] | None = None
    roles: list[Role] | None = None
    schema_names: dict = attrs.field(factory=dict, eq=False, hash=False)

    def __attrs_post_init__(self):
        if self.users is None:
            self.users = []
        if self.groups is None:
            self.groups = []
        if self.roles is None:
            self.roles = []

    @classmethod
    def from_redshift_connector(cls, connector: RedshiftConnector) -> Specification:
        """Initialize a Specification from a RedshiftConnector.

        The entire load runs inside a single ``connector.connect()`` block, so
        the cluster-level queries (users, groups, databases, schemas) reuse one
        physical connection instead of opening one per query.
        """
        connect = getattr(connector, "connect", None)
        cm = connect() if callable(connect) else contextlib.nullcontext()
        with cm:
            return cls._load_from_connector(connector)

    @classmethod
    def _load_from_connector(cls, connector: RedshiftConnector) -> Specification:
        users, groups = cls.fetch_users_and_groups(connector)
        schema_names: dict = {}

        user_idx = {user.name: idx for idx, user in enumerate(users)}
        group_idx = {group.name: idx for idx, group in enumerate(groups)}

        public_privileges = Privileges()

        get_table_parts = operator.attrgetter(
            "database_name", "schema_name", "table_name"
        )
        get_schema_parts = operator.attrgetter("database_name", "schema_name")

        for entity in itertools.chain(
            connector.iter_tables(),
            connector.iter_schemas(),
            connector.iter_databases(),
        ):
            if isinstance(entity, Table):
                db_obj = DatabaseObject.from_parts(
                    *get_table_parts(entity),
                    type=DatabaseObjectType[entity.table_type],
                )
            elif isinstance(entity, Database):
                db_obj = DatabaseObject.from_parts(
                    entity.database_name,
                    type=DatabaseObjectType.DATABASE,
                )
            elif isinstance(entity, Schema):
                db_obj = DatabaseObject.from_parts(
                    *get_schema_parts(entity),
                    type=DatabaseObjectType.SCHEMA,
                )
                schema_names.setdefault(entity.database_name, []).append(
                    entity.schema_name
                )

            owner = entity.owner
            users[user_idx[owner]].add_owned_db_object(db_obj)

            for holder_name, holder_type, action in entity.iter_acl():
                try:
                    action = Action(action)
                except ValueError:
                    # Unrecognized ACL privilege code (e.g. Redshift-specific
                    # extensions not in the Action enum). Skip rather than crash.
                    continue

                if action in (Action.TRIGGER, Action.RULE):
                    # These are not really used by Redshift.
                    # IDK why they pop up in ACLs.
                    continue

                privilege = Privilege(database_object=db_obj, action=action)

                if holder_name == "PUBLIC":
                    public_privileges.add(privilege)
                    continue

                try:
                    if holder_type == "user":
                        users[user_idx[holder_name]].add_privilege(privilege)
                    elif holder_type == "group":
                        groups[group_idx[holder_name]].add_privilege(privilege)

                except KeyError:
                    # I think this is a deleted user/group
                    continue

        if len(public_privileges) > 0:
            public_user = User(
                name="PUBLIC",
                is_superuser=False,
                privileges=public_privileges,
                owns=None,
                groups=None,
            )
            users.append(public_user)

        return cls(users=users, groups=groups, schema_names=schema_names)

    @staticmethod
    def fetch_users_and_groups(
        connector: RedshiftConnector,
    ) -> tuple[list[User], list[Group]]:
        groups: list[Group] = []
        group_members: dict[int, set[str]] = {}

        for group_row in connector.iter_groups():
            group = Group(
                name=group_row.groname,
                privileges=None,
            )
            groups.append(group)

            for user_id in group_row.iter_group_members():
                user_groups = group_members.setdefault(user_id, set())
                user_groups.add(group.name)

        users: list[User] = []

        for user_row in connector.iter_users():
            user = User(
                name=user_row.usename,
                is_superuser=user_row.usesuper,
                privileges=None,
                owns=None,
                groups=group_members.get(user_row.usesysid),
            )
            users.append(user)

        return users, groups

    @classmethod
    def from_yaml_file(cls, path) -> Specification:
        """Initialize a Specification from a YAML file path."""
        with open(path) as f:
            yaml_str = f.read()
        return cls.from_yaml(yaml_str)

    def group_to_users(self) -> Iterator[tuple[Group, list[User]]]:
        if self.groups is None:
            return

        for group in self.groups:
            users = [user for user in self.users if group.name in user.groups]
            yield group, users

    def user_to_groups(self) -> Iterator[tuple[User, list[Group]]]:
        if self.users is None:
            return

        for user in self.users:
            if user.groups is None or len(user.groups) == 0:
                continue

            if self.groups is None:
                groups = []
            else:
                groups = [group for group in self.groups if group.name in user.groups]
            yield user, groups

    def validate(
        self, require_owner: bool = False
    ) -> tuple[bool, list[ValidationFailure] | None]:
        """Validate this configuration.

        Args:
            require_owner (bool): When True, validation fails unless every
                DatabaseObject referenced by a privilege has a declared owner
                (i.e. appears in some User's ``owns``).

        Returns:
            tuple: first value indicates whether validation was successful.
                Second value contains a list of ValidationFailures or is None
                if validation was successful.
        """
        _, failures = self.check_users_belong_to_existing_groups()

        if failures is None:
            failures = []

        _, role_reference_failures = self.check_users_belong_to_existing_roles()
        if role_reference_failures is not None:
            failures.extend(role_reference_failures)

        _, role_membership_failures = self.check_roles_belong_to_existing_roles()
        if role_membership_failures is not None:
            failures.extend(role_membership_failures)

        for user in self.users:
            _, user_failures = user.validate()
            if user_failures is not None:
                try:
                    failures.extend(user_failures)
                except AttributeError:
                    failures = user_failures

        for group in self.groups:
            _, group_failures = group.validate()
            if group_failures is not None:
                try:
                    failures.extend(group_failures)
                except AttributeError:
                    failures = group_failures

        for role in self.roles:
            _, role_failures = role.validate()
            if role_failures is not None:
                try:
                    failures.extend(role_failures)
                except AttributeError:
                    failures = role_failures

        if require_owner is True:
            _, owner_failures = self.check_objects_have_owners()
            if owner_failures is not None:
                failures.extend(owner_failures)

        if len(failures) == 0:
            return True, None
        return False, failures

    def check_objects_have_owners(
        self,
    ) -> tuple[bool, list[ValidationFailure] | None]:
        """Check every privileged DatabaseObject has a declared owner.

        An object is considered owned if it appears in some User's ``owns``.
        Returns a ValidationFailure for each privileged object that is not.

        Returns:
            tuple: first value indicates whether the check succeeded. Second
                value is a list of ValidationFailures, or None on success.
        """
        users = self.users if self.users is not None else []
        groups = self.groups if self.groups is not None else []

        owned: set[DatabaseObject] = set()
        for user in users:
            if user.owns is not None:
                owned.update(user.owns)

        failures: list[ValidationFailure] = []
        seen: set[DatabaseObject] = set()

        subjects: list[User | Group] = [*users, *groups]
        for subject in subjects:
            if subject.privileges is None:
                continue

            for privilege in subject.privileges:
                db_obj = privilege.database_object
                if db_obj in owned or db_obj in seen:
                    continue

                seen.add(db_obj)
                failures.append(
                    ValidationFailure(
                        subject=db_obj,
                        message=f"{db_obj} has no declared owner",
                    )
                )

        if len(failures) == 0:
            return True, None
        return False, failures

    def check_users_belong_to_existing_groups(
        self,
    ) -> tuple[bool, list[ValidationFailure] | None]:
        """Check Users are members of Groups in this Specification.

        Specification should contain all users and groups. Which means
        that a user cannot belong to a group that is not part of this
        Specification.

        Returns:
            tuple: first value indicates whether check was successful.
                Second value contains a list of ValidationFailures or is None
                if validation was successful.
        """
        success = True
        failures = None
        for user, groups in self.user_to_groups():
            # len mismatches would mean a group appears in groups
            # but not in self.groups. The inverse could also be true,
            # but we are not looking to validate that as we don't know
            # which groups should a user belong to.
            if len(groups) == len(user.groups):
                continue

            non_existing_groups = [
                group
                for group in user.groups
                if group not in [group.name for group in groups]
            ]

            failure = ValidationFailure(
                subject=user,
                message=f"User is member of non declared groups: {non_existing_groups}",
            )
            success = False
            try:
                failures.append(failure)
            except AttributeError:
                failures = [failure]

        return success, failures

    def check_users_belong_to_existing_roles(
        self,
    ) -> tuple[bool, list[ValidationFailure] | None]:
        """Check Users only reference Roles declared in this Specification."""
        success = True
        failures = None
        role_names = {role.name for role in self.roles}

        for user in self.users:
            if user.roles is None or len(user.roles) == 0:
                continue

            non_existing_roles = [role for role in user.roles if role not in role_names]
            if len(non_existing_roles) == 0:
                continue

            failure = ValidationFailure(
                subject=user,
                message=f"User is member of non declared roles: {non_existing_roles}",
            )
            success = False
            try:
                failures.append(failure)
            except AttributeError:
                failures = [failure]

        return success, failures

    def check_roles_belong_to_existing_roles(
        self,
    ) -> tuple[bool, list[ValidationFailure] | None]:
        """Check Roles' ``member_of`` only reference Roles declared in this Specification."""
        success = True
        failures = None
        role_names = {role.name for role in self.roles}

        for role in self.roles:
            if role.member_of is None or len(role.member_of) == 0:
                continue

            non_existing_roles = [
                member for member in role.member_of if member not in role_names
            ]
            if len(non_existing_roles) == 0:
                continue

            failure = ValidationFailure(
                subject=role,
                message=f"Role is member of non declared roles: {non_existing_roles}",
            )
            success = False
            try:
                failures.append(failure)
            except AttributeError:
                failures = [failure]

        return success, failures
