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
class ServiceSettings:
    api_name: str = "tg-api-zapret"
    public_base_url: str | None = None
    default_api_interface: str = "rest"
    enabled_interfaces: list[str] = field(
        default_factory=lambda: ["rest", "json_rpc", "websocket", "sse", "queue", "python_sdk"]
    )
    max_queue_jobs_list: int = 1000
    stream_queue_size: int = 100
    request_timeout_seconds: int = 60
    expose_docs: bool = True
    cors_origins: list[str] = field(default_factory=list)
    require_api_token: bool = False
    api_token_env: str = "TG_API_TOKEN"
    api_tokens_env: str = "TG_API_TOKENS"
    rate_limit_per_minute: int = 120
    audit_log_path: str | None = None
    enable_raw_invoke: bool = True
    enable_layer_invoke: bool = True
    bot_token_accounts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ServiceSettings":
        if not data:
            return cls()
        return cls(
            api_name=data.get("api_name") or cls.api_name,
            public_base_url=data.get("public_base_url") or None,
            default_api_interface=data.get("default_api_interface") or cls.default_api_interface,
            enabled_interfaces=normalize_interfaces(data.get("enabled_interfaces")),
            max_queue_jobs_list=int(data.get("max_queue_jobs_list", cls.max_queue_jobs_list)),
            stream_queue_size=int(data.get("stream_queue_size", cls.stream_queue_size)),
            request_timeout_seconds=int(
                data.get("request_timeout_seconds", cls.request_timeout_seconds)
            ),
            expose_docs=bool(data.get("expose_docs", cls.expose_docs)),
            cors_origins=list(data.get("cors_origins") or []),
            require_api_token=bool(data.get("require_api_token", cls.require_api_token)),
            api_token_env=data.get("api_token_env") or cls.api_token_env,
            api_tokens_env=data.get("api_tokens_env") or cls.api_tokens_env,
            rate_limit_per_minute=int(
                data.get("rate_limit_per_minute", cls.rate_limit_per_minute)
            ),
            audit_log_path=data.get("audit_log_path") or None,
            enable_raw_invoke=bool(data.get("enable_raw_invoke", cls.enable_raw_invoke)),
            enable_layer_invoke=bool(data.get("enable_layer_invoke", cls.enable_layer_invoke)),
            bot_token_accounts={
                str(token): normalize_account_name(account)
                for token, account in dict(data.get("bot_token_accounts") or {}).items()
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "public_base_url": self.public_base_url,
            "default_api_interface": self.default_api_interface,
            "enabled_interfaces": self.enabled_interfaces,
            "max_queue_jobs_list": self.max_queue_jobs_list,
            "stream_queue_size": self.stream_queue_size,
            "request_timeout_seconds": self.request_timeout_seconds,
            "expose_docs": self.expose_docs,
            "cors_origins": self.cors_origins,
            "require_api_token": self.require_api_token,
            "api_token_env": self.api_token_env,
            "api_tokens_env": self.api_tokens_env,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "audit_log_path": self.audit_log_path,
            "enable_raw_invoke": self.enable_raw_invoke,
            "enable_layer_invoke": self.enable_layer_invoke,
            "bot_token_accounts": self.bot_token_accounts,
        }


@dataclass(frozen=True)
class AppSettings:
    proxy_url: str | None = None
    client_profile: ClientProfile = field(default_factory=ClientProfile)
    service: ServiceSettings = field(default_factory=ServiceSettings)
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
            service=ServiceSettings.from_dict(data.get("service")),
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
                    "service": self.service.to_dict(),
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
            service=self.service,
            active_account=account_name,
            accounts=accounts,
        )


def parse_proxy_url(proxy_url: str) -> tuple[Any, ...]:
    parsed = validate_proxy_url(proxy_url)
    scheme = parsed.scheme.lower()
    proxy_type = "http" if scheme == "https" else "socks5" if scheme == "socks5h" else scheme
    rdns = scheme in {"https", "socks5h"}

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
    if scheme not in {"http", "https", "socks5", "socks5h"}:
        raise ValueError("Proxy URL must use http, https, socks5, or socks5h scheme")
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


def normalize_interfaces(interfaces: list[str] | None) -> list[str]:
    allowed = {"rest", "json_rpc", "websocket", "sse", "queue", "python_sdk"}
    values = []
    for interface in interfaces or ["rest", "json_rpc", "websocket", "sse", "queue", "python_sdk"]:
        if interface in allowed and interface not in values:
            values.append(interface)
    return values or ["rest"]
