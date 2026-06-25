"""Unit tests for the CLI module."""

from __future__ import annotations

from unittest import mock

import pytest
import yaml
from typer.testing import CliRunner

from redtape.admin import OnError
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
                        "member_of": ["analysts"],
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
                        "member_of": ["ghost_group"],
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
                        "member_of": ["missing_group"],
                    }
                ],
                "groups": [],
            }
        )
    )
    result = runner.invoke(app, ["validate", "--json", str(spec_path)])
    assert result.exit_code == 1


def _patched_run(monkeypatch):
    """Patch the run command's DB-touching collaborators.

    Returns the Mock standing in for ``admin.manage`` so callers can assert
    how the command invoked it (in particular, the ``on_error`` argument).
    """
    manage = mock.Mock(return_value=(True, []))
    admin = mock.Mock()
    admin.manage = manage
    admin.ops = [mock.Mock()]
    admin.queries = mock.Mock(return_value=[("SELECT 1", admin.ops[0])])

    trainer = mock.Mock()
    trainer.train = mock.Mock(return_value=admin)

    monkeypatch.setattr(
        "redtape.cli.DatabaseAdministratorTrainer",
        mock.Mock(return_value=trainer),
    )
    monkeypatch.setattr("redtape.cli.RedshiftConnector", mock.Mock())
    monkeypatch.setattr(
        "redtape.cli.load_spec",
        mock.Mock(return_value=mock.Mock()),
    )
    monkeypatch.setattr(
        "redtape.cli.validate_spec",
        mock.Mock(return_value=(True, None)),
    )
    return manage


def test_run_default_uses_on_error_continue(valid_spec_file, monkeypatch):
    """Without --atomic, run applies queries with OnError.CONTINUE."""
    manage = _patched_run(monkeypatch)

    result = runner.invoke(app, ["run", str(valid_spec_file)])

    assert result.exit_code == 0
    assert manage.call_args.kwargs["on_error"] is OnError.CONTINUE


def test_run_atomic_uses_on_error_abort(valid_spec_file, monkeypatch):
    """--atomic makes run apply queries with OnError.ABORT for rollback."""
    manage = _patched_run(monkeypatch)

    result = runner.invoke(app, ["run", "--atomic", str(valid_spec_file)])

    assert result.exit_code == 0
    assert manage.call_args.kwargs["on_error"] is OnError.ABORT
