import pytest
import yaml


@pytest.fixture(scope="session")
def spec_file(tmp_path_factory):
    """Create a test configuration file."""
    p = tmp_path_factory.mktemp("config") / "redtape.yml"
    content = yaml.safe_dump(
        {
            "users": [
                {
                    "name": "test_user_1",
                    "is_superuser": True,
                    "groups": ["my_user_group_1", "my_user_group_2"],
                    "privileges": {
                        "table": {
                            "read": [
                                "one_table",
                                "another_table",
                                "database_name.*.*",
                            ],
                        },
                        "schema": {
                            "write": [
                                "a_schema",
                                "database_name.*",
                            ]
                        },
                        "database": {
                            "read": ["my_db"],
                        },
                    },
                }
            ]
        }
    )
    p.write_text(content)
    return p
