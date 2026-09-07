"""Unit tests for the CLI module."""

from __future__ import annotations

import pytest
import yaml
from typer.testing import CliRunner

from redtape.cli import app

runner = CliRunner()


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
