import pytest

from tg_api_zapret.config import OFFICIAL_DESKTOP_API_HASH, OFFICIAL_DESKTOP_API_ID, TelegramConfig


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

