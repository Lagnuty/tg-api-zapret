from types import SimpleNamespace

from fastapi.testclient import TestClient
from telethon.tl.types import User

from tg_api_zapret.api import (
    ApiState,
    create_app,
    normalize_username_entity,
    serialize_dialog,
    telegram_action_limit,
)
from tg_api_zapret.config import ServiceSettings


def test_docs_are_disabled_by_default(tmp_path) -> None:
    app = create_app(
        ApiState(config_file=str(tmp_path / "config.json"), session_file=str(tmp_path / "s.txt"))
    )
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/docs").status_code == 404


def test_api_token_required_by_default(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TG_API_TOKEN", "secret")
    app = create_app(
        ApiState(config_file=str(tmp_path / "config.json"), session_file=str(tmp_path / "s.txt"))
    )
    client = TestClient(app)

    assert client.get("/accounts").status_code == 401
    response = client.get("/accounts", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.json()["accounts"] == ["default"]


def test_blocked_demo_account_name_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TG_API_TOKEN", "secret")
    app = create_app(
        ApiState(config_file=str(tmp_path / "config.json"), session_file=str(tmp_path / "s.txt"))
    )
    client = TestClient(app)

    response = client.post(
        "/accounts",
        headers={"Authorization": "Bearer secret"},
        json={"account": "string"},
    )

    assert response.status_code == 400
    assert "Unsafe demo account name" in response.json()["detail"]


def test_capabilities_show_full_rpc_methods(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TG_API_TOKEN", "secret")
    app = create_app(
        ApiState(config_file=str(tmp_path / "config.json"), session_file=str(tmp_path / "s.txt"))
    )
    client = TestClient(app)

    response = client.get("/capabilities", headers={"Authorization": "Bearer secret"})
    data = response.json()
    methods = data["interfaces"]["json_rpc"]["methods"]
    bot_methods = response.json()["interfaces"]["bot_api_compat"]["methods"]
    rest_endpoints = data["interfaces"]["rest"]["endpoints"]

    assert "messages.edit" in methods
    assert "media.send" in methods
    assert "messages.send_username" in methods
    assert "tl.construct" in methods
    assert "sendMessage" in bot_methods
    assert "getUpdates" in bot_methods
    assert "POST /accounts/connect" in rest_endpoints
    assert "GET /accounts/online" in rest_endpoints
    assert "GET /accounts/health" in rest_endpoints
    assert "GET /accounts/risk-status" in rest_endpoints
    assert "POST /accounts/entity-cache/warm" in rest_endpoints
    assert "GET /accounts/entity-cache" in rest_endpoints
    assert "POST /messages/list" in rest_endpoints


def test_dialog_serializer_includes_username_and_input_entity() -> None:
    user = User(id=123, access_hash=456, username="alice", first_name="Alice")
    dialog = SimpleNamespace(
        id=123,
        name="Alice",
        title="Alice",
        entity=user,
        is_user=True,
        is_group=False,
        is_channel=False,
        unread_count=0,
    )

    serialized = serialize_dialog(dialog)

    assert serialized["username"] == "alice"
    assert serialized["access_hash"] == 456
    assert serialized["input_entity"]["_"] == "InputPeerUser"


def test_normalize_username_entity() -> None:
    assert normalize_username_entity("alice") == "@alice"
    assert normalize_username_entity("@alice") == "@alice"
    assert normalize_username_entity("https://t.me/alice") == "@alice"
    assert normalize_username_entity("+79990000000") == "+79990000000"


def test_risk_status_endpoint_exposes_safe_limits(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TG_API_TOKEN", "secret")
    app = create_app(
        ApiState(config_file=str(tmp_path / "config.json"), session_file=str(tmp_path / "s.txt"))
    )
    client = TestClient(app)

    response = client.get("/accounts/risk-status", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    data = response.json()
    assert data["accounts"]["default"]["safe_mode"] is True
    assert data["limits"]["telegram_send_actions_per_minute"] == 6


def test_telegram_action_limits_are_risk_weighted() -> None:
    service = ServiceSettings()

    assert telegram_action_limit(service, "messages.send") == (6, 60)
    assert telegram_action_limit(service, "raw.invoke") == (3, 60)
    assert telegram_action_limit(service, "chats.join") == (5, 3600)
    assert telegram_action_limit(service, "admin.ban") == (10, 3600)
