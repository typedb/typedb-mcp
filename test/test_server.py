import asyncio
import json

import pytest
import requests
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

import common
import config
import server

READ_TOOLS = {"query", "database_list", "database_schema"}
ALL_TOOLS = READ_TOOLS | {"database_create", "database_delete", "user_list", "user_create", "user_delete"}


@pytest.fixture(autouse=True)
def restore_config(monkeypatch):
    # build_server and main write module globals; monkeypatch restores them after each test
    for name in ("READ_ONLY", "TOKEN_REUSE", "TYPEDB_URL", "TYPEDB_USERNAME", "TYPEDB_PASSWORD"):
        monkeypatch.setattr(config, name, getattr(config, name))
    monkeypatch.setattr(common, "_token", None)
    monkeypatch.delenv("TYPEDB_PASSWORD", raising=False)


@pytest.fixture
def http(monkeypatch):
    """Replace Session.request; records (method, url, kwargs) and answers 200 with an empty JSON object."""
    calls = []

    def fake(session, method, url, **kwargs):
        calls.append((method, url, kwargs))
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps({"token": "t"} if url.endswith("/v1/signin") else {}).encode()
        return r

    monkeypatch.setattr(requests.sessions.Session, "request", fake)
    monkeypatch.setattr(config, "TYPEDB_URL", "http://typedb.test")
    return calls


def with_client(read_only, fn):
    async def go():
        async with Client(server.build_server(read_only=read_only)) as client:
            return await fn(client)
    return asyncio.run(go())


def tool_names(read_only):
    async def fn(c):
        return {t.name for t in await c.list_tools()}
    return with_client(read_only, fn)


def call_query(read_only, tx):
    async def fn(c):
        return await c.call_tool("query", {"query": "match $x isa y;", "database": "d", "transaction_type": tx})
    return with_client(read_only, fn)


def test_read_only_tool_set():
    assert tool_names(True) == READ_TOOLS


def test_default_tool_set():
    assert tool_names(False) == ALL_TOOLS


def test_read_only_rejects_write_without_http(http):
    with pytest.raises(ToolError, match="read-only"):
        call_query(True, "write")
    assert http == []


def test_read_query_posts_read_transaction(http):
    call_query(True, "read")
    posts = [c for c in http if c[1].endswith("/v1/query")]
    assert len(posts) == 1
    assert posts[0][0] == "POST"
    assert posts[0][2]["json"]["transactionType"] == "read"
    assert posts[0][2]["json"]["commit"] is False


def test_password_from_env(monkeypatch):
    monkeypatch.setenv("TYPEDB_PASSWORD", "from-env")
    assert server.parse_args(["--typedb-address", "http://x"]).typedb_password == "from-env"


def test_explicit_password_wins(monkeypatch):
    monkeypatch.setenv("TYPEDB_PASSWORD", "from-env")
    args = server.parse_args(["--typedb-address", "http://x", "--typedb-password", "explicit"])
    assert args.typedb_password == "explicit"


def test_host_defaults_to_loopback_and_accepts_any_interface():
    assert server.parse_args(["--typedb-address", "http://x"]).host == "127.0.0.1"
    assert server.parse_args(["--typedb-address", "http://x", "--host", "0.0.0.0"]).host == "0.0.0.0"


@pytest.fixture
def run_main(monkeypatch):
    """Call server.main with FastMCP.run and the signal handlers stubbed; returns the run() kwargs."""
    seen = {}
    monkeypatch.setattr(FastMCP, "run", lambda self, **kw: seen.update(kw))
    monkeypatch.setattr(server.signal, "signal", lambda *a: None)

    def go(*argv):
        server.main(["--typedb-address", "http://x", *argv])
        return seen

    return go


def test_main_passes_host_and_port(run_main):
    seen = run_main("--host", "0.0.0.0", "--port", "9123")
    assert (seen["host"], seen["port"]) == ("0.0.0.0", 9123)


def test_token_reuse_default_and_switch(run_main):
    run_main()
    assert config.TOKEN_REUSE is True
    run_main("--no-token-reuse")
    assert config.TOKEN_REUSE is False


def test_help_never_prints_env_password(monkeypatch, capsys):
    monkeypatch.setenv("TYPEDB_PASSWORD", "s3cret-value")
    with pytest.raises(SystemExit):
        server.parse_args(["--help"])
    assert "s3cret-value" not in capsys.readouterr().out
