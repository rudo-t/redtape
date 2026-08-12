from __future__ import annotations

from unittest import mock

import redtape.connectors as db
from redtape.connectors import RedshiftConnector, parse_acl


def test_parse_acl():
    """Test the parse_acl function with a few sample ACLs."""
    acl_1 = "{user1=arwdRxtD/user1,group group1=arw/user1,group group2=U*/user1}"

    result_1 = [acl for acl in parse_acl(acl_1, sep=",")]
    expected_1 = [
        ("user1", "user", "a"),
        ("user1", "user", "r"),
        ("user1", "user", "w"),
        ("user1", "user", "d"),
        ("user1", "user", "R"),
        ("user1", "user", "x"),
        ("user1", "user", "t"),
        ("user1", "user", "D"),
        ("group1", "group", "a"),
        ("group1", "group", "r"),
        ("group1", "group", "w"),
        ("group2", "group", "U*"),
    ]
    assert result_1 == expected_1

    acl_2 = "{user2=a*r*w*d*/user2,group group2=U*D*/user2}"

    result_2 = [acl for acl in parse_acl(acl_2, sep=",")]
    expected_2 = [
        ("user2", "user", "a*"),
        ("user2", "user", "r*"),
        ("user2", "user", "w*"),
        ("user2", "user", "d*"),
        ("group2", "group", "U*"),
        ("group2", "group", "D*"),
    ]
    assert result_2 == expected_2

    acl_3 = "=T/user3,user3=CT/user3,user4=C/user3"

    result_3 = [acl for acl in parse_acl(acl_3, sep=",")]
    expected_3 = [
        ("PUBLIC", "PUBLIC", "T"),
        ("user3", "user", "C"),
        ("user3", "user", "T"),
        ("user4", "user", "C"),
    ]
    assert result_3 == expected_3


def test_parse_acl_none():
    """parse_acl with None yields nothing without raising."""
    assert list(parse_acl(None)) == []


def test_parse_acl_empty_string():
    """parse_acl with an empty string yields nothing."""
    assert list(parse_acl("")) == []


def test_group_iter_group_members_none():
    """iter_group_members yields nothing when grolist is None."""
    group = db.Group(groname="empty", grosysid=1, grolist=None)
    assert list(group.iter_group_members()) == []


def test_group_iter_group_members_populated():
    """iter_group_members yields each user id in order."""
    group = db.Group(groname="members", grosysid=2, grolist=[100, 101, 102])
    assert list(group.iter_group_members()) == [100, 101, 102]


def _make_connector(**overrides) -> RedshiftConnector:
    kwargs = {
        "dbname": "a_db",
        "host": "cluster.example.com",
        "port": 5439,
        "user": "admin",
        "password": "secret",
    }
    kwargs.update(overrides)
    return RedshiftConnector(**kwargs)


def test_default_sslmode_is_verify_full():
    """A RedshiftConnector defaults to verified TLS unless told otherwise."""
    connector = _make_connector()

    assert connector.sslmode == "verify-full"
    assert connector.sslrootcert is None


def test_open_connection_requests_verified_tls_by_default():
    """open_connection asks psycopg2 for a verified, encrypted connection by default."""
    connector = _make_connector()

    with mock.patch.object(db.psycopg2, "connect") as mock_connect:
        connector.open_connection()

    _, kwargs = mock_connect.call_args
    assert kwargs["sslmode"] == "verify-full"
    assert "sslrootcert" not in kwargs


def test_open_connection_honors_overridden_sslmode_and_sslrootcert():
    """Overriding sslmode/sslrootcert via config changes what psycopg2.connect receives."""
    connector = _make_connector(
        sslmode="verify-ca", sslrootcert="/etc/redtape/redshift-ca-bundle.pem"
    )

    with mock.patch.object(db.psycopg2, "connect") as mock_connect:
        connector.open_connection()

    _, kwargs = mock_connect.call_args
    assert kwargs["sslmode"] == "verify-ca"
    assert kwargs["sslrootcert"] == "/etc/redtape/redshift-ca-bundle.pem"
