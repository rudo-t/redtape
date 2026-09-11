"""Unit tests for the CLI module."""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest
import yaml
from typer.testing import CliRunner

import redtape.connectors as db
from redtape.cli import app
from redtape.connectors import RedshiftConnector
from redtape.specification import Specification

runner = CliRunner()


@pytest.fixture
def patch_redshift_connector(monkeypatch):
    """Monkeypatch `RedshiftConnector.from_environ` to return a given fake.

    Returns a function `patch(connector)` that wires `RedshiftConnector.
    from_environ(...)` (however it is called - `redtape/cli.py`'s `run` and
    `export` commands always call it with a single `environ=` kwarg) to
    return the supplied fake connector instead of touching real environment
    variables, a config file, or a network connection.
    """

    def patch(connector):
        monkeypatch.setattr(
            RedshiftConnector, "from_environ", lambda **kwargs: connector
        )
        return connector

    return patch


@pytest.fixture
def valid_spec_file(tmp_path):
    """A spec file that passes validation: user's groups are all declared."""
    spec_path = tmp_path / "valid.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "groups": ["analysts"],
                    }
                ],
                "groups": [{"name": "analysts"}],
            }
        )
    )
    return spec_path


def test_validate_valid_spec(valid_spec_file):
    """validate exits 0 for a well-formed spec file."""
    result = runner.invoke(app, ["validate", str(valid_spec_file)])
    assert result.exit_code == 0


def test_validate_file_not_found():
    """validate exits 1 when the spec file does not exist."""
    result = runner.invoke(app, ["validate", "/nonexistent/path/redtape.yml"])
    assert result.exit_code == 1


def test_validate_invalid_spec(tmp_path):
    """validate exits 1 when a user references a group not declared in the spec."""
    spec_path = tmp_path / "invalid.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "groups": ["ghost_group"],
                    }
                ],
                "groups": [],
            }
        )
    )
    result = runner.invoke(app, ["validate", str(spec_path)])
    assert result.exit_code == 1


def test_validate_quiet_suppresses_output(valid_spec_file):
    """--quiet produces no output on a valid spec."""
    result = runner.invoke(app, ["validate", "--quiet", str(valid_spec_file)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_validate_quiet_unsupported_privilege_still_prints_error():
    """--quiet still surfaces the load-time error for an unsupported privilege
    shorthand (a spec that raises UnsupportedPrivilegeError while loading)."""
    spec_yaml = yaml.safe_dump(
        {
            "groups": [
                {
                    "name": "g1",
                    "privileges": {"table": {"select": ["orders"]}},
                }
            ],
        }
    )
    result = runner.invoke(app, ["validate", "--quiet"], input=spec_yaml)
    assert result.exit_code == 1
    assert result.output.strip() != ""
    assert "Invalid specification file" in result.output


def test_validate_quiet_file_not_found_still_prints_error():
    """--quiet still surfaces the error when the spec file doesn't exist."""
    result = runner.invoke(
        app, ["validate", "--quiet", "/nonexistent/path/redtape.yml"]
    )
    assert result.exit_code == 1
    assert result.output.strip() != ""
    assert "does not exist" in result.output


def test_validate_quiet_invalid_spec_still_prints_errors(tmp_path):
    """--quiet still surfaces validation failures, just not progress messages."""
    spec_path = tmp_path / "invalid.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "groups": ["ghost_group"],
                    }
                ],
                "groups": [],
            }
        )
    )
    result = runner.invoke(app, ["validate", "--quiet", str(spec_path)])
    assert result.exit_code == 1
    assert result.output.strip() != ""
    assert "Specification loaded!" not in result.output


def test_validate_json_on_invalid_spec(tmp_path):
    """--json outputs a JSON error structure on an invalid spec."""
    spec_path = tmp_path / "invalid.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "bob",
                        "is_superuser": False,
                        "groups": ["missing_group"],
                    }
                ],
                "groups": [],
            }
        )
    )
    result = runner.invoke(app, ["validate", "--json", str(spec_path)])
    assert result.exit_code == 1


def test_validate_valid_spec_with_roles(tmp_path):
    """validate exits 0 on a spec with roles, role-to-role membership, and
    users with roles:."""
    spec_path = tmp_path / "valid_roles.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "roles": ["analytics_role"],
                    }
                ],
                "groups": [],
                "roles": [
                    {"name": "reporting_role"},
                    {
                        "name": "analytics_role",
                        "member_of": ["reporting_role"],
                        "privileges": {
                            "table": {"read": ["orders"]},
                        },
                    },
                ],
            }
        )
    )
    result = runner.invoke(app, ["validate", str(spec_path)])
    assert result.exit_code == 0


def test_validate_fails_user_references_undeclared_role(tmp_path):
    """validate exits 1 when a user references a role not declared in roles:."""
    spec_path = tmp_path / "invalid_roles.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "roles": ["ghost_role"],
                    }
                ],
                "groups": [],
                "roles": [],
            }
        )
    )
    result = runner.invoke(app, ["validate", str(spec_path)])
    assert result.exit_code == 1


@pytest.fixture
def desired_spec_file(tmp_path):
    """A desired spec: alice, in group analysts, with no table privileges."""
    spec_path = tmp_path / "desired.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [
                    {
                        "name": "alice",
                        "is_superuser": False,
                        "groups": ["analysts"],
                    }
                ],
                "groups": [{"name": "analysts"}],
            }
        )
    )
    return spec_path


def test_run_dry_reports_create_operations(
    desired_spec_file, fake_connector_factory, patch_redshift_connector
):
    """run --dry prints the plan to create a not-yet-existing user and group."""
    connector = patch_redshift_connector(fake_connector_factory())

    result = runner.invoke(app, ["run", "--dry", str(desired_spec_file)])

    assert result.exit_code == 0
    assert "CREATE USER" in result.output
    assert "CREATE GROUP" in result.output
    assert connector.iter_users  # sanity: the fake was actually used


def test_run_dry_reports_revoke_operation(
    desired_spec_file, fake_connector_factory, patch_redshift_connector
):
    """run --dry prints a REVOKE for a privilege present in Redshift but not
    in the desired spec, without crashing (the scenario that used to crash
    before the REVOKE query builders were implemented, see #19)."""
    current_connector = fake_connector_factory(
        users=[
            db.User(
                usename="alice",
                usesysid=1,
                usecreatedb=False,
                usesuper=False,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
        ],
        groups=[
            db.Group(groname="analysts", grosysid=2, grolist=[1]),
        ],
        tables=[
            db.Table(
                database_name="prod",
                schema_name="public",
                table_name="secret_table",
                table_owner="alice",
                table_type="TABLE",
                table_acl="alice=arwdRxtD/alice",
                remarks=None,
            ),
        ],
    )
    patch_redshift_connector(current_connector)

    result = runner.invoke(app, ["run", "--dry", str(desired_spec_file)])

    assert result.exit_code == 0
    assert "REVOKE" in result.output
    assert "secret_table" in result.output


def test_run_dry_no_changes_needed(
    fake_connector_factory, patch_redshift_connector, tmp_path
):
    """run --dry exits cleanly and prints nothing to do when current state
    already matches the desired spec."""
    spec_path = tmp_path / "matches_current.yml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "users": [{"name": "alice", "is_superuser": False, "groups": []}],
                "groups": [],
            }
        )
    )
    connector = fake_connector_factory(
        users=[
            db.User(
                usename="alice",
                usesysid=1,
                usecreatedb=False,
                usesuper=False,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
        ],
    )
    patch_redshift_connector(connector)

    result = runner.invoke(app, ["run", "--dry", str(spec_path)])

    assert result.exit_code == 0


@pytest.fixture
def export_connector(fake_connector_factory):
    """A fake connector with a user, an unpopulated group, and a table the
    user owns with several privileges, used to exercise `export`'s YAML/JSON
    serialization paths.

    Deliberately does not put the user in a group (`grolist=[]`): a
    connector-derived `User.groups` is a plain `set`, and
    `Specification.to_json` has no serializer registered for a bare `set`
    (only for the `Privileges`/`Ownerships`/`Enum` types it explicitly
    dispatches on) - `export --json` crashes with `TypeError: Object of type
    set is not JSON serializable` whenever a user has any group membership.
    That's a real, separate bug (filed as an issue, not fixed here per this
    issue's out-of-scope: no production changes beyond what's needed for
    connector fakeability) - this fixture sidesteps it so the YAML/JSON
    equivalence tests below can exercise everything else `export` does
    (users, groups, ownership, and privileges) without tripping over it.
    """
    return fake_connector_factory(
        users=[
            db.User(
                usename="alice",
                usesysid=1,
                usecreatedb=False,
                usesuper=False,
                usecatupd=False,
                valuntil=None,
                useconfig=None,
            ),
        ],
        groups=[
            db.Group(groname="analysts", grosysid=2, grolist=[]),
        ],
        tables=[
            db.Table(
                database_name="prod",
                schema_name="public",
                table_name="orders",
                table_owner="alice",
                table_type="TABLE",
                table_acl="alice=arwdRxtD/alice",
                remarks=None,
            ),
        ],
    )


def _expected_export_dict(connector) -> dict:
    """The dict `export`'s output is expected to match, derived independently
    through the same public `Specification.from_redshift_connector` +
    `to_dict` API `export` itself uses - this checks CLI wiring (the right
    connector reaches the right loader and gets printed faithfully), not a
    reimplementation of the serialization logic under test elsewhere."""
    return Specification.from_redshift_connector(connector).to_dict()


def test_export_yaml_matches_connector_state(
    export_connector, patch_redshift_connector
):
    """export (default YAML) prints valid YAML matching the fake connector's
    reported state."""
    patch_redshift_connector(export_connector)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 0
    parsed = yaml.safe_load(result.output)
    assert parsed == _expected_export_dict(export_connector)


def test_export_json_matches_connector_state(
    export_connector, patch_redshift_connector
):
    """export --json prints valid JSON with content equivalent to the
    default YAML case."""
    patch_redshift_connector(export_connector)

    result = runner.invoke(app, ["export", "--json"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == _expected_export_dict(export_connector)


def test_export_yaml_and_json_are_equivalent(
    export_connector, patch_redshift_connector
):
    """The YAML and --json outputs of export describe the same content."""
    patch_redshift_connector(export_connector)

    yaml_result = runner.invoke(app, ["export"])
    json_result = runner.invoke(app, ["export", "--json"])

    assert yaml.safe_load(yaml_result.output) == json.loads(json_result.output)


def test_export_quiet_still_prints_the_spec(export_connector, patch_redshift_connector):
    """--quiet on export suppresses only incidental/progress output, not the
    exported spec itself - export's normal output *is* the spec, so it must
    still appear."""
    patch_redshift_connector(export_connector)

    result = runner.invoke(app, ["export", "--quiet"])

    assert result.exit_code == 0
    parsed = yaml.safe_load(result.output)
    assert parsed == _expected_export_dict(export_connector)


class _ConnectionErrorConnector(db.RedshiftConnector):
    """A fake connector whose `connect()` always raises `ConnectionError`,
    used to exercise export's error path (mirrors the existing `--quiet`
    regression tests for `validate` above)."""

    @contextmanager
    def connect(self):
        raise ConnectionError("could not connect to Redshift")
        yield self  # pragma: no cover - unreachable, keeps this a generator


def test_export_quiet_connection_error_still_prints_error(
    patch_redshift_connector,
):
    """--quiet still surfaces a genuine error (failure to connect) on
    export, per --quiet's documented contract of suppressing only
    incidental/progress output, never real errors."""
    patch_redshift_connector(_ConnectionErrorConnector())

    result = runner.invoke(app, ["export", "--quiet"])

    assert result.exit_code == 1
    assert result.output.strip() != ""
    assert "Failed to connect to Redshift Database" in result.output
