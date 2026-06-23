from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.main import app

client = TestClient(app)


def test_login_and_jwt_me(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    login = client.post(
        "/api/v1/auth/login",
        json={"user_id": "admin-1", "password": "changeme"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    assert token

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()["data"]
    assert body["user_id"] == "admin-1"
    assert body["role_id"] == "admin"


def test_session_cookie_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    login = client.post(
        "/api/v1/auth/login",
        json={"user_id": "engineer-1", "password": "changeme"},
    )
    assert login.status_code == 200
    cookie = login.cookies.get("amx_session")
    assert cookie

    me = client.get("/api/v1/auth/me", cookies={"amx_session": cookie})
    assert me.status_code == 200
    assert me.json()["data"]["role_id"] == "process_engineer"
