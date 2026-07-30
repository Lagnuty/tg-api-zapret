import pytest

from tg_api_zapret import __version__
from tg_api_zapret.config import (
    OFFICIAL_DESKTOP_API_HASH,
    OFFICIAL_DESKTOP_API_ID,
    AppSettings,
    TelegramConfig,
    parse_proxy_url,
)


def test_config_uses_official_desktop_defaults() -> None:
    config = TelegramConfig()

    assert config.api_id == OFFICIAL_DESKTOP_API_ID
    assert config.api_hash == OFFICIAL_DESKTOP_API_HASH
    assert config.device_model == "Telegram Desktop"
    assert config.system_version == "Linux x86_64"
    assert config.app_version == __version__


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_API_ID", "123")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash")
    monkeypatch.setenv("TELEGRAM_TIMEOUT", "7")

    config = TelegramConfig.from_env()

    assert config.api_id == 123
    assert config.api_hash == "hash"
    assert config.timeout == 7


@pytest.mark.parametrize(
    ("proxy_url", "proxy_type", "rdns"),
    [
        ("http://127.0.0.1:8080", "http", False),
        ("https://127.0.0.1:8080", "http", True),
        ("socks5://127.0.0.1:1080", "socks5", False),
        ("socks5h://127.0.0.1:1080", "socks5", True),
    ],
)
def test_parse_proxy_url(proxy_url: str, proxy_type: str, rdns: bool) -> None:
    parsed = parse_proxy_url(proxy_url)

    assert parsed[:4] == (proxy_type, "127.0.0.1", int(proxy_url.rsplit(":", 1)[1]), rdns)


def test_parse_proxy_url_with_auth() -> None:
    parsed = parse_proxy_url("socks5h://user:password@127.0.0.1:1080")

    assert parsed == ("socks5", "127.0.0.1", 1080, True, "user", "password")


def test_app_settings_roundtrip(tmp_path) -> None:
    path = tmp_path / "config.json"

    AppSettings(proxy_url="socks5h://127.0.0.1:1080").save(path)

    assert AppSettings.load(path).proxy_url == "socks5h://127.0.0.1:1080"


def test_app_settings_client_profile_roundtrip(tmp_path) -> None:
    path = tmp_path / "config.json"
    settings = AppSettings.load(path)
    custom = settings.client_profile.__class__(
        device_model="custom-api",
        system_version="Ubuntu",
        app_version="custom-api",
        lang_code="ru",
        system_lang_code="ru-RU",
    )

    AppSettings(proxy_url=None, client_profile=custom).save(path)
    loaded = AppSettings.load(path)

    assert loaded.client_profile.device_model == "custom-api"
    assert loaded.client_profile.system_lang_code == "ru-RU"


def test_legacy_client_profile_app_version_migrates_to_package_version(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        """
        {
          "client_profile": {
            "device_model": "tg-api-zapret",
            "system_version": "Linux",
            "app_version": "tg-api-zapret"
          }
        }
        """,
        encoding="utf-8",
    )

    loaded = AppSettings.load(path)

    assert loaded.client_profile.app_version == __version__


def test_app_settings_accounts_roundtrip(tmp_path) -> None:
    path = tmp_path / "config.json"

    AppSettings().with_account("work account").save(path)
    loaded = AppSettings.load(path)

    assert loaded.active_account == "work_account"
    assert loaded.accounts == ["default", "work_account"]


def test_partial_service_settings_uses_safety_defaults(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"service":{"rate_limit_per_minute":10}}', encoding="utf-8")

    loaded = AppSettings.load(path)

    assert loaded.service.rate_limit_per_minute == 10
    assert loaded.service.blocked_account_names == ["string", "account"]
    assert loaded.service.telegram_min_action_interval_seconds == 1.25
    assert loaded.service.telegram_safe_mode is True
    assert loaded.service.telegram_serialize_account_actions is True
    assert loaded.service.telegram_send_actions_per_minute == 6
    assert loaded.service.telegram_raw_actions_per_minute == 3
    assert loaded.service.telegram_join_actions_per_hour == 5
    assert loaded.service.telegram_destructive_actions_per_hour == 10
    assert loaded.service.telegram_default_flood_cooldown_seconds == 300
    assert loaded.service.keep_accounts_online is True
    assert loaded.service.online_update_interval_seconds == 55
    assert loaded.service.auto_connect_accounts == []
    assert loaded.service.reconnect_enabled is True
    assert loaded.service.passive_update_receiver is True
    assert loaded.service.entity_cache_warmup_dialogs == 50
    assert loaded.service.require_connection_health_before_auth is True
