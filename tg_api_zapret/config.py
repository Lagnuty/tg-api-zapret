from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tg_api_zapret.version import __version__

OFFICIAL_DESKTOP_API_ID = 2040
OFFICIAL_DESKTOP_API_HASH = "b18441a1ff607e10a989891a5462e627"


@dataclass(frozen=True)
class TelegramConfig:
    api_id: int = OFFICIAL_DESKTOP_API_ID
    api_hash: str = OFFICIAL_DESKTOP_API_HASH
    device_model: str = "tg-api-zapret"
    system_version: str = "Linux"
    app_version: str = __version__
    lang_code: str = "en"
    system_lang_code: str = "en-US"
    request_retries: int = 5
    connection_retries: int = 5
    retry_delay: int = 2
    timeout: int = 30
    proxy: tuple[Any, ...] | None = None

    @classmethod
    def from_env(
        cls,
        *,
        proxy_url: str | None = None,
        client_profile: "ClientProfile | None" = None,
    ) -> "TelegramConfig":
        resolved_proxy_url = proxy_url or os.getenv("TELEGRAM_PROXY_URL")
        profile = client_profile or ClientProfile()
        return cls(
            api_id=int(os.getenv("TELEGRAM_API_ID", OFFICIAL_DESKTOP_API_ID)),
            api_hash=os.getenv("TELEGRAM_API_HASH", OFFICIAL_DESKTOP_API_HASH),
            device_model=os.getenv("TELEGRAM_DEVICE_MODEL", profile.device_model),
            system_version=os.getenv("TELEGRAM_SYSTEM_VERSION", profile.system_version),
            app_version=os.getenv("TELEGRAM_APP_VERSION", profile.app_version),
            lang_code=os.getenv("TELEGRAM_LANG_CODE", profile.lang_code),
            system_lang_code=os.getenv("TELEGRAM_SYSTEM_LANG_CODE", profile.system_lang_code),
            request_retries=int(os.getenv("TELEGRAM_REQUEST_RETRIES", "5")),
            connection_retries=int(os.getenv("TELEGRAM_CONNECTION_RETRIES", "5")),
            retry_delay=int(os.getenv("TELEGRAM_RETRY_DELAY", "2")),
            timeout=int(os.getenv("TELEGRAM_TIMEOUT", "30")),
            proxy=parse_proxy_url(resolved_proxy_url) if resolved_proxy_url else None,
        )


@dataclass(frozen=True)
class ClientProfile:
    device_model: str = "tg-api-zapret"
    system_version: str = "Linux"
    app_version: str = __version__
    lang_code: str = "en"
    system_lang_code: str = "en-US"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ClientProfile":
        if not data:
            return cls()
        return cls(
            device_model=data.get("device_model") or cls.device_model,
            system_version=data.get("system_version") or cls.system_version,
            app_version=normalize_app_version(data.get("app_version")),
            lang_code=data.get("lang_code") or cls.lang_code,
            system_lang_code=data.get("system_lang_code") or cls.system_lang_code,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "device_model": self.device_model,
            "system_version": self.system_version,
            "app_version": self.app_version,
            "lang_code": self.lang_code,
            "system_lang_code": self.system_lang_code,
        }


@dataclass(frozen=True)
class AppSettings:
    proxy_url: str | None = None
    client_profile: ClientProfile = field(default_factory=ClientProfile)
    active_account: str = "default"
    accounts: list[str] = field(default_factory=lambda: ["default"])

    @classmethod
    def load(cls, path: str | Path) -> "AppSettings":
        settings_path = Path(path).expanduser()
        if not settings_path.exists():
            return cls()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        return cls(
            proxy_url=data.get("proxy_url") or None,
            client_profile=ClientProfile.from_dict(data.get("client_profile")),
            active_account=data.get("active_account") or "default",
            accounts=normalize_accounts(data.get("accounts")),
        )

    def save(self, path: str | Path) -> None:
        settings_path = Path(path).expanduser()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "proxy_url": self.proxy_url,
                    "client_profile": self.client_profile.to_dict(),
                    "active_account": self.active_account,
                    "accounts": normalize_accounts(self.accounts),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            settings_path.chmod(0o600)
        except OSError:
            pass

    def with_account(self, account: str) -> "AppSettings":
        account_name = normalize_account_name(account)
        accounts = normalize_accounts([*self.accounts, account_name])
        return AppSettings(
            proxy_url=self.proxy_url,
            client_profile=self.client_profile,
            active_account=account_name,
            accounts=accounts,
        )


def parse_proxy_url(proxy_url: str) -> tuple[Any, ...]:
    parsed = validate_proxy_url(proxy_url)
    scheme = parsed.scheme.lower()
    proxy_type = "http" if scheme == "https" else "socks5" if scheme in {"socks5d", "socks5h"} else scheme
    rdns = scheme in {"https", "socks5d", "socks5h"}

    return (
        proxy_type,
        parsed.hostname,
        parsed.port,
        rdns,
        parsed.username,
        parsed.password,
    )


def validate_proxy_url(proxy_url: str):
    parsed = urlparse(proxy_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "socks5", "socks5d", "socks5h"}:
        raise ValueError("Proxy URL must use http, https, socks5, socks5d, or socks5h scheme")
    if not parsed.hostname or not parsed.port:
        raise ValueError("Proxy URL must include host and port")
    return parsed


def normalize_accounts(accounts: list[str] | None) -> list[str]:
    values = []
    for account in accounts or ["default"]:
        normalized = normalize_account_name(account)
        if normalized not in values:
            values.append(normalized)
    return values or ["default"]


def normalize_account_name(account: str | None) -> str:
    value = (account or "default").strip()
    if not value:
        return "default"
    allowed = []
    for char in value:
        if char.isalnum() or char in {"-", "_", "."}:
            allowed.append(char)
        else:
            allowed.append("_")
    return "".join(allowed)


def normalize_app_version(app_version: str | None) -> str:
    if not app_version or app_version == "tg-api-zapret":
        return __version__
    return app_version
