import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import config
from server import build_server

pytestmark = pytest.mark.integration

READ_TOOLS = {"query", "database_list", "database_schema"}
ALL_TOOLS = READ_TOOLS | {"database_create", "database_delete", "user_list", "user_create", "user_delete"}


def run(read_only, fn):
    async def go():
        async with Client(build_server(read_only=read_only)) as client:
            return await fn(client)
    return asyncio.run(go())


@pytest.fixture(autouse=True)
def restore_read_only(monkeypatch):
    monkeypatch.setattr(config, "READ_ONLY", False)


def test_read_only_tool_set():
    async def fn(c):
        return {t.name for t in await c.list_tools()}
    assert run(True, fn) == READ_TOOLS


def test_full_tool_set():
    async def fn(c):
        return {t.name for t in await c.list_tools()}
    assert run(False, fn) == ALL_TOOLS


def test_read_query_works(temp_db):
    async def fn(c):
        r = await c.call_tool("query", {
            "query": "match $i isa item; fetch { $i.* };",
            "database": temp_db,
            "transaction_type": "read",
        })
        return r.content[0].text
    assert "ITEM-0001" in run(True, fn)


@pytest.mark.parametrize("tx", ["write", "schema", "READ", " read"])
def test_non_read_transactions_rejected(temp_db, tx):
    async def fn(c):
        await c.call_tool("query", {
            "query": 'insert $i isa item, has item-id "ITEM-0003";',
            "database": temp_db,
            "transaction_type": tx,
        })
    with pytest.raises(ToolError, match="read-only"):
        run(True, fn)


def test_write_tools_absent():
    async def fn(c):
        await c.call_tool("database_create", {"name": "mcp_it_never"})
    with pytest.raises(ToolError):
        run(True, fn)


def test_database_list_and_schema(temp_db):
    async def fn(c):
        dbs = (await c.call_tool("database_list", {})).content[0].text
        schema = (await c.call_tool("database_schema", {"name": temp_db})).content[0].text
        return dbs, schema
    dbs, schema = run(True, fn)
    assert temp_db in dbs
    assert "item-id" in schema
