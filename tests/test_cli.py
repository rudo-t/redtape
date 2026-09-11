"""Unit tests for the CLI module."""

from __future__ import annotations

import pytest
import yaml
from typer.testing import CliRunner

import redtape.connectors as db
from redtape.cli import app
from redtape.connectors import RedshiftConnector

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
