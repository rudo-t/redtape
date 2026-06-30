"""Fixtures for integration tests.

Run with: pytest tests/integration/ -m integration

These tests exercise redtape's real Redshift SQL (export uses Redshift-only
system views and ``VARCHAR(MAX)``), so they require a **real Redshift cluster**
— a Postgres-based emulator such as pgredshift cannot run the read/export path.

Point the tests at a cluster with the ``REDTAPE_INTEGRATION_DSN`` environment
variable (a libpq DSN). In CI this comes from a repository secret. If the DSN
is unset or the cluster is unreachable, the whole suite **skips** rather than
fails, so it is safe to run anywhere and is kept non-blocking in CI.

Connection defaults match the docker-compose.yml service for ad-hoc local DDL
experiments, but note the export tests will not pass against pgredshift.

Tests that require Redshift features not yet covered (RBAC roles, ASSUMEROLE,
out-of-band grants, etc.) are individually marked with ``pytest.mark.skip``.
"""

from __future__ import annotations

import os

import psycopg2
import pytest

INTEGRATION_DSN = os.environ.get(
    "REDTAPE_INTEGRATION_DSN",
    "host=localhost port=5439 dbname=test_db user=test_admin password=TestPassword1",
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires a real Redshift cluster (set REDTAPE_INTEGRATION_DSN)",
    )


@pytest.fixture(scope="session")
def connector():
    """Return a RedshiftConnector pointed at the test cluster.

    RedshiftConnector parses a libpq DSN passed as ``db_url`` in
    ``__attrs_post_init__`` (see ``parse_db_url``), so the connection
    parameters come straight from ``INTEGRATION_DSN``.

    Probes connectivity once up front; if no cluster is reachable the whole
    integration suite skips (instead of erroring) so it stays non-blocking.
    """
    from redtape.connectors import RedshiftConnector

    conn = RedshiftConnector(db_url=INTEGRATION_DSN)
    try:
        with conn.connect():
            pass
    except (psycopg2.Error, ConnectionError) as e:
        pytest.skip(f"no reachable Redshift cluster for integration tests: {e}")
    return conn


@pytest.fixture(autouse=True)
def require_integration(request):
    """Skip any test in this directory unless -m integration is passed."""
    if request.node.get_closest_marker("integration") is None:
        pytest.skip("integration tests require -m integration")
