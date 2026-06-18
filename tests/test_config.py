import pytest

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
        ("socks5d://127.0.0.1:1080", "socks5", True),
        ("socks5h://127.0.0.1:1080", "socks5", True),
    ],
)
def test_parse_proxy_url(proxy_url: str, proxy_type: str, rdns: bool) -> None:
    parsed = parse_proxy_url(proxy_url)

    assert parsed[:4] == (proxy_type, "127.0.0.1", int(proxy_url.rsplit(":", 1)[1]), rdns)


def test_parse_proxy_url_with_auth() -> None:
    parsed = parse_proxy_url("socks5d://user:password@127.0.0.1:1080")

    assert parsed == ("socks5", "127.0.0.1", 1080, True, "user", "password")


def test_app_settings_roundtrip(tmp_path) -> None:
    path = tmp_path / "config.json"

    AppSettings(proxy_url="socks5d://127.0.0.1:1080").save(path)

    assert AppSettings.load(path).proxy_url == "socks5d://127.0.0.1:1080"
