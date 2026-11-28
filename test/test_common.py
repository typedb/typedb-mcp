import json

import pytest
import requests

import common
import config
import database
import query as query_mod
import user


class FakeTypeDB:
    """Stands in for requests.sessions.Session.request; answers from a script of status codes."""

    def __init__(self):
        self.calls = []  # (method, url, kwargs)
        self.statuses = []  # status codes for non-signin calls, consumed in order; default 200
        self.signins = 0

    def __call__(self, session, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        r = requests.Response()
        if url.endswith("/v1/signin"):
            self.signins += 1
            r.status_code = 200
            r._content = json.dumps({"token": f"t{self.signins}"}).encode()
            return r
        r.status_code = self.statuses.pop(0) if self.statuses else 200
        r._content = json.dumps({"code": "AUT3", "message": "invalid"} if r.status_code == 401 else {"ok": True}).encode()
        return r

    def api_calls(self):
        return [c for c in self.calls if not c[1].endswith("/v1/signin")]


@pytest.fixture
def fake(monkeypatch):
    f = FakeTypeDB()
    monkeypatch.setattr(requests.sessions.Session, "request", lambda session, method, url, **kw: f(session, method, url, **kw))
    monkeypatch.setattr(common, "_token", None)
    monkeypatch.setattr(config, "TYPEDB_URL", "http://typedb.test")
    monkeypatch.setattr(config, "TOKEN_REUSE", True)
    monkeypatch.setattr(config, "READ_ONLY", False)
    return f


def test_token_reused_across_calls(fake):
    common.typedb_request("GET", "/v1/databases")
    common.typedb_request("GET", "/v1/databases")
    assert fake.signins == 1
    assert [c[2]["headers"]["Authorization"] for c in fake.api_calls()] == ["Bearer t1", "Bearer t1"]


def test_401_signs_in_once_more_and_retries(fake):
    fake.statuses = [401, 200]
    r = common.typedb_request("GET", "/v1/databases")
    assert r.status_code == 200
    assert fake.signins == 2
    assert len(fake.api_calls()) == 2
    assert fake.api_calls()[1][2]["headers"]["Authorization"] == "Bearer t2"


def test_second_401_is_returned_without_loop(fake):
    fake.statuses = [401, 401, 200]
    r = common.typedb_request("GET", "/v1/databases")
    assert r.status_code == 401
    assert len(fake.api_calls()) == 2
    with pytest.raises(requests.HTTPError):
        common.handle_typedb_response(r)


def test_no_token_reuse_signs_in_per_call(fake, monkeypatch):
    monkeypatch.setattr(config, "TOKEN_REUSE", False)
    common.typedb_request("GET", "/v1/databases")
    common.typedb_request("GET", "/v1/databases")
    assert fake.signins == 2


def test_no_token_reuse_still_retries_401_once(fake, monkeypatch):
    monkeypatch.setattr(config, "TOKEN_REUSE", False)
    fake.statuses = [401, 200]
    r = common.typedb_request("GET", "/v1/databases")
    assert r.status_code == 200
    assert fake.signins == 2
    assert len(fake.api_calls()) == 2


def test_every_request_has_timeout(fake):
    common.typedb_request("GET", "/v1/databases")
    common.typedb_request("GET", "/v1/databases", timeout=5)
    signin = [c for c in fake.calls if c[1].endswith("/v1/signin")][0]
    assert signin[2]["timeout"] == 10
    assert [c[2]["timeout"] for c in fake.api_calls()] == [60, 5]



def test_tool_modules_use_upstream_paths_and_one_signin(fake):
    database.list_databases()
    database.create_database("d")
    database.delete_database("d")
    database.database_schema("d")
    user.list_users()
    user.create_user("u", "pw")
    user.delete_user("u")
    query_mod.query("match $x isa y;", "d", "write")
    assert fake.signins == 1
    got = [(m, u.removeprefix("http://typedb.test")) for m, u, _ in fake.api_calls()]
    assert got == [
        ("GET", "/v1/databases"),
        ("POST", "/v1/databases/d"),
        ("DELETE", "/v1/databases/d"),
        ("GET", "/v1/databases/d/schema"),
        ("GET", "/v1/users"),
        ("POST", "/v1/users/u"),
        ("DELETE", "/v1/users/u"),
        ("POST", "/v1/query"),
    ]
    assert fake.api_calls()[5][2]["json"] == {"password": "pw"}
    assert fake.api_calls()[7][2]["json"] == {
        "databaseName": "d", "transactionType": "write", "query": "match $x isa y;", "commit": True,
    }



def test_header_uses_own_token_when_another_thread_resets_the_cache(fake, monkeypatch):
    """Another thread clearing the shared cache between sign-in and the request must not yield 'Bearer None'."""

    class RacingConfig:
        TOKEN_REUSE = False
        TYPEDB_USERNAME = TYPEDB_PASSWORD = "x"

        @property
        def TYPEDB_URL(self):
            common._token = None  # what a concurrent call does at its start
            return "http://typedb.test"

    monkeypatch.setattr(common, "config", RacingConfig())
    common.typedb_request("GET", "/v1/databases")
    assert fake.api_calls()[0][2]["headers"]["Authorization"] == "Bearer t1"


def test_path_segments_are_url_encoded(fake):
    database.database_schema("x/../../users?")
    database.create_database("a b")
    database.delete_database("a/b")
    user.create_user("u/../x", "pw")
    user.delete_user("u?")
    got = [u.removeprefix("http://typedb.test") for _, u, _ in fake.api_calls()]
    assert got == [
        "/v1/databases/x%2F..%2F..%2Fusers%3F/schema",
        "/v1/databases/a%20b",
        "/v1/databases/a%2Fb",
        "/v1/users/u%2F..%2Fx",
        "/v1/users/u%3F",
    ]


def test_database_schema_cannot_reach_other_endpoints(fake):
    """requests normalizes dot segments in the path, so the encoded name must stay one segment on the wire."""
    database.database_schema("x/../../users?")
    prepared = requests.Request("GET", fake.api_calls()[0][1]).prepare()
    assert prepared.path_url == "/v1/databases/x%2F..%2F..%2Fusers%3F/schema"
