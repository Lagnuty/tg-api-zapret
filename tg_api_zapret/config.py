from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
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
    def from_env(cls, *, proxy_url: str | None = None) -> "TelegramConfig":
        resolved_proxy_url = proxy_url or os.getenv("TELEGRAM_PROXY_URL")
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
            proxy=parse_proxy_url(resolved_proxy_url) if resolved_proxy_url else None,
        )


@dataclass(frozen=True)
class AppSettings:
    proxy_url: str | None = None

    @classmethod
    def load(cls, path: str | Path) -> "AppSettings":
        settings_path = Path(path).expanduser()
        if not settings_path.exists():
            return cls()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        return cls(proxy_url=data.get("proxy_url") or None)

    def save(self, path: str | Path) -> None:
        settings_path = Path(path).expanduser()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"proxy_url": self.proxy_url}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        try:
            settings_path.chmod(0o600)
        except OSError:
            pass


def parse_proxy_url(proxy_url: str) -> tuple[Any, ...]:
    parsed = urlparse(proxy_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "socks5", "socks5d", "socks5h"}:
        raise ValueError("Proxy URL must use http, https, socks5, socks5d, or socks5h scheme")

    try:
        import socks
    except ImportError as exc:  # pragma: no cover - dependency is declared.
        raise RuntimeError("PySocks is required for proxy support") from exc

    proxy_type = {
        "http": socks.HTTP,
        "https": socks.HTTP,
        "socks5": socks.SOCKS5,
        "socks5d": socks.SOCKS5,
        "socks5h": socks.SOCKS5,
    }[scheme]
    if not parsed.hostname or not parsed.port:
        raise ValueError("Proxy URL must include host and port")

    rdns = scheme in {"https", "socks5d", "socks5h"}

    return (
        proxy_type,
        parsed.hostname,
        parsed.port,
        rdns,
        parsed.username,
        parsed.password,
    )
