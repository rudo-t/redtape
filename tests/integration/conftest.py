"""Fixtures for integration tests.

Run with: pytest tests/integration/ -m integration

Requires a running Redshift-compatible database. Start one with:
    docker compose up -d

Connection defaults match the docker-compose.yml service.

Tests that require a real Redshift cluster (RBAC roles, ASSUMEROLE, etc.)
are marked pytest.mark.skip(reason="requires real Redshift cluster").
"""

from __future__ import annotations

import os

import pytest

INTEGRATION_DSN = os.environ.get(
    "REDTAPE_INTEGRATION_DSN",
    "host=localhost port=5439 dbname=test_db user=test_admin password=TestPassword1",
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires a running Redshift-compatible database",
    )


@pytest.fixture(scope="session")
def connector():
    """Return a RedshiftConnector pointed at the test database."""
    from redtape.connectors import RedshiftConnector

    # INTEGRATION_DSN is a libpq keyword/value string, which psycopg2's
    # parse_dsn (used by RedshiftConnector.parse_db_url via db_url) understands.
    return RedshiftConnector(db_url=INTEGRATION_DSN)


@pytest.fixture(autouse=True)
def require_integration(request):
    """Skip any test in this directory unless -m integration is passed."""
    if request.node.get_closest_marker("integration") is None:
        pytest.skip("integration tests require -m integration")
