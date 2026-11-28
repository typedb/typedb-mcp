import os
import secrets

import pytest
import requests

import config
import database
from query import query


@pytest.fixture(scope="session", autouse=True)
def typedb_it():
    """Point the server modules at the TypeDB named by TYPEDB_IT_URL; skip without it."""
    url = os.environ.get("TYPEDB_IT_URL")
    if not url:
        pytest.skip("TYPEDB_IT_URL not set")
    password = os.environ.get("TYPEDB_PASSWORD")
    if not password:
        pytest.fail("TYPEDB_PASSWORD must be set when TYPEDB_IT_URL is set")
    config.TYPEDB_URL = url
    config.TYPEDB_USERNAME = "admin"
    config.TYPEDB_PASSWORD = password


@pytest.fixture
def temp_db():
    """Throwaway database with two synthetic items; deleted afterwards."""
    config.READ_ONLY = False
    name = "mcp_it_" + secrets.token_hex(4)
    database.create_database(name)
    try:
        query("define attribute item-id, value string; entity item, owns item-id @key;", name, "schema")
        query('insert $a isa item, has item-id "ITEM-0001"; $b isa item, has item-id "ITEM-0002";', name, "write")
        yield name
    finally:
        config.READ_ONLY = False
        try:
            database.delete_database(name)
        except requests.HTTPError as e:
            body = e.args[0] if e.args and isinstance(e.args[0], dict) else {}
            # This build answers a missing database with 400 DBD1, not 404.
            if e.response.status_code != 404 and body.get("code") != "DBD1":
                raise
