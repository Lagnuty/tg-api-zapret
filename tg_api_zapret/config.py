from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any
from urllib.parse import urlparse

OFFICIAL_DESKTOP_API_ID = 2040
OFFICIAL_DESKTOP_API_HASH = "b18441a1ff607e10a989891a5462e627"


@dataclass(frozen=True)
class TelegramConfig:
    api_id: int = OFFICIAL_DESKTOP_API_ID
    api_hash: str = OFFICIAL_DESKTOP_API_HASH
    device_model: str = "Desktop"
    system_version: str = "Linux"
    app_version: str = "5.0"
    lang_code: str = "en"
    system_lang_code: str = "en-US"
    request_retries: int = 5
    connection_retries: int = 5
    retry_delay: int = 2
    timeout: int = 30
    proxy: tuple[Any, ...] | None = None

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        proxy_url = os.getenv("TELEGRAM_PROXY_URL")
        return cls(
            api_id=int(os.getenv("TELEGRAM_API_ID", OFFICIAL_DESKTOP_API_ID)),
            api_hash=os.getenv("TELEGRAM_API_HASH", OFFICIAL_DESKTOP_API_HASH),
            device_model=os.getenv("TELEGRAM_DEVICE_MODEL", "Desktop"),
            system_version=os.getenv("TELEGRAM_SYSTEM_VERSION", "Linux"),
            app_version=os.getenv("TELEGRAM_APP_VERSION", "5.0"),
            lang_code=os.getenv("TELEGRAM_LANG_CODE", "en"),
            system_lang_code=os.getenv("TELEGRAM_SYSTEM_LANG_CODE", "en-US"),
            request_retries=int(os.getenv("TELEGRAM_REQUEST_RETRIES", "5")),
            connection_retries=int(os.getenv("TELEGRAM_CONNECTION_RETRIES", "5")),
            retry_delay=int(os.getenv("TELEGRAM_RETRY_DELAY", "2")),
            timeout=int(os.getenv("TELEGRAM_TIMEOUT", "30")),
            proxy=parse_proxy_url(proxy_url) if proxy_url else None,
        )


def parse_proxy_url(proxy_url: str) -> tuple[Any, ...]:
    parsed = urlparse(proxy_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"socks4", "socks5", "http"}:
        raise ValueError("TELEGRAM_PROXY_URL must use socks4, socks5, or http scheme")

    try:
        import socks
    except ImportError as exc:  # pragma: no cover - dependency is declared.
        raise RuntimeError("PySocks is required for proxy support") from exc

    proxy_type = {
        "socks4": socks.SOCKS4,
        "socks5": socks.SOCKS5,
        "http": socks.HTTP,
    }[scheme]
    if not parsed.hostname or not parsed.port:
        raise ValueError("TELEGRAM_PROXY_URL must include host and port")

    return (
        proxy_type,
        parsed.hostname,
        parsed.port,
        True,
        parsed.username,
        parsed.password,
    )

