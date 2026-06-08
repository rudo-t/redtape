"""Integration tests: export spec from a live database."""

from __future__ import annotations

import pytest

from redtape.specification import Specification


@pytest.mark.integration
def test_export_produces_valid_spec(connector):
    """Spec exported from a live DB passes validation."""
    spec = Specification.from_redshift_connector(connector)
    success, failures = spec.validate()
    assert success is True, f"Exported spec failed validation: {failures}"


@pytest.mark.integration
def test_export_roundtrip_yaml(connector):
    """Spec exported from a live DB survives a YAML roundtrip."""
    spec = Specification.from_redshift_connector(connector)
    yaml_str = spec.to_yaml()
    restored = Specification.from_yaml(yaml_str)
    assert len(restored.users) == len(spec.users)
    assert len(restored.groups) == len(spec.groups)


@pytest.mark.integration
def test_export_schema_names_not_in_yaml(connector):
    """schema_names must not appear in the exported YAML."""
    spec = Specification.from_redshift_connector(connector)
    assert "schema_names" not in spec.to_yaml()
