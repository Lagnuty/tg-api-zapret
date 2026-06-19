from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from telethon import events, utils
from telethon.errors import FloodWaitError, PasswordHashInvalidError, RPCError, SessionPasswordNeededError
from telethon.tl import functions, types
from telethon.tl.custom.dialog import Dialog
from telethon.tl.custom.message import Message
from telethon.tl.types import User

from tg_api_zapret.client import SentCode, TelegramLayer
from tg_api_zapret.config import (
    AppSettings,
    ClientProfile,
    ServiceSettings,
    TelegramConfig,
    normalize_account_name,
    validate_proxy_url,
)
from tg_api_zapret.mtproto_layers import get_layer_functions, require_layer_function
from tg_api_zapret.queue_backends import QueueBackend, build_queue_backend
from tg_api_zapret.sessions import FileSessionBackend, SQLiteSessionBackend, TelethonSessionFileBackend
from tg_api_zapret.tl_codec import (
    build_tl_object,
    build_tl_request,
    resolve_entity,
    serialize_tl,
)
from tg_api_zapret.version import __version__

REQUEST_SCOPES: ContextVar[list[str] | None] = ContextVar("REQUEST_SCOPES", default=None)


class ApiState:
    def __init__(
        self,
        *,
        config_file: str,
        session_file: str,
        session_db: str | None = None,
        default_account: str = "default",
        queue_backend: str = "memory",
        redis_url: str | None = None,
    ) -> None:
        self.config_file = Path(config_file).expanduser()
        self.session_file = Path(session_file).expanduser()
        self.session_db = Path(session_db).expanduser() if session_db else None
        self.default_account = normalize_account_name(default_account)
        self.layers: dict[str, TelegramLayer] = {}
        service = self.settings().service
        self.queue: QueueBackend = build_queue_backend(
            queue_backend,
            redis_url=redis_url,
            visibility_timeout_seconds=service.queue_visibility_timeout_seconds,
        )
        self.rate_limits: dict[str, list[float]] = {}
        self.telegram_rate_limits: dict[str, list[float]] = {}
        self.telegram_auth_rate_limits: dict[str, list[float]] = {}
        self.last_telegram_action_at: dict[str, float] = {}
        self.bot_updates: dict[str, list[dict[str, Any]]] = {}
        self.bot_update_ids: dict[str, int] = {}
        self.bot_update_handlers: dict[str, tuple[Any, Any]] = {}
        self.online_tasks: dict[str, asyncio.Task[None]] = {}
        self.online_status: dict[str, dict[str, Any]] = {}
        self.reconnect_tasks: dict[str, asyncio.Task[None]] = {}
        self.update_handlers: dict[str, tuple[Any, Any]] = {}
        self.entity_cache: dict[str, dict[str, dict[str, Any]]] = {}
        self.connection_health: dict[str, dict[str, Any]] = {}

    async def startup(self) -> None:
        service = self.settings().service
        for account in service.auto_connect_accounts:
            try:
                layer = await self.connect(account)
                if await layer.is_authorized():
                    await self.activate_desktop_like_runtime(account)
            except Exception as exc:
                account_name = normalize_account_name(account)
                self.connection_health[account_name] = {
                    "account": account_name,
                    "ok": False,
                    "error": str(exc),
                    "last_check_ts": int(time.time()),
                }

    def settings(self) -> AppSettings:
        return AppSettings.load(self.config_file)

    def save_settings(self, settings: AppSettings) -> None:
        settings.save(self.config_file)

    async def connect(self, account: str | None = None) -> TelegramLayer:
        account_name = self.resolve_account(account)
        settings = self.settings()
        if self.session_db:
            backend = SQLiteSessionBackend(self.session_db, account_name)
        else:
            session_path = resolve_session_file(self.session_file, account_name)
            if account_name == "default" and session_path.suffix == ".session":
                backend = TelethonSessionFileBackend(session_path)
            else:
                backend = FileSessionBackend(session_path)
        layer = TelegramLayer(
            TelegramConfig.from_env(
                proxy_url=settings.proxy_url,
                client_profile=settings.client_profile,
            ),
            backend,
        )
        await layer.connect()
        self.layers[account_name] = layer
        if account_name not in settings.accounts:
            self.save_settings(settings.with_account(account_name))
        if settings.service.keep_accounts_online and await layer.is_authorized():
            await self.activate_desktop_like_runtime(account_name)
        return layer

    async def disconnect(self, account: str | None = None) -> None:
        if account is None:
            for account_name in list(self.online_tasks):
                await self.stop_online_keepalive(account_name)
            for account_name in list(self.reconnect_tasks):
                await self.stop_reconnect_loop(account_name)
            for account_name in list(self.update_handlers):
                await self.stop_passive_update_receiver(account_name)
            for layer in self.layers.values():
                await layer.disconnect()
            self.layers.clear()
            await self.queue.close()
            return
        account_name = self.resolve_account(account)
        await self.stop_online_keepalive(account_name)
        await self.stop_reconnect_loop(account_name)
        await self.stop_passive_update_receiver(account_name)
        layer = self.layers.pop(account_name, None)
        if layer:
            await layer.disconnect()

    async def require_layer(self, account: str | None = None) -> TelegramLayer:
        account_name = self.resolve_account(account)
        if account_name not in self.layers:
            return await self.connect(account_name)
        return self.layers[account_name]

    def resolve_account(self, account: str | None = None) -> str:
        account_name = normalize_account_name(account or self.settings().active_account or self.default_account)
        service = self.settings().service
        blocked = {normalize_account_name(item) for item in service.blocked_account_names}
        if account_name in blocked:
            raise ValueError(
                f"Unsafe demo account name '{account_name}' is blocked. "
                "Choose a real account alias, for example main/work/personal."
            )
        return account_name

    def start_online_keepalive(self, account: str) -> None:
        account_name = self.resolve_account(account)
        task = self.online_tasks.get(account_name)
        if task and not task.done():
            return
        self.online_tasks[account_name] = asyncio.create_task(self._online_keepalive_loop(account_name))

    async def activate_desktop_like_runtime(self, account: str) -> None:
        account_name = self.resolve_account(account)
        service = self.settings().service
        if service.keep_accounts_online:
            self.start_online_keepalive(account_name)
        if service.passive_update_receiver:
            await self.start_passive_update_receiver(account_name)
        if service.entity_cache_warmup_dialogs > 0:
            await self.warm_entity_cache(account_name, limit=service.entity_cache_warmup_dialogs)
        if service.reconnect_enabled:
            self.start_reconnect_loop(account_name)

    async def stop_online_keepalive(self, account: str) -> None:
        account_name = self.resolve_account(account)
        task = self.online_tasks.pop(account_name, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        layer = self.layers.get(account_name)
        if layer and await layer.is_authorized():
            try:
                client = await layer.authorized_client()
                await client(functions.account.UpdateStatusRequest(offline=True))
            except Exception:
                pass
        self.online_status[account_name] = {
            "account": account_name,
            "keep_online": False,
            "last_update_ts": int(time.time()),
        }

    async def _online_keepalive_loop(self, account: str) -> None:
        while True:
            interval = max(15, self.settings().service.online_update_interval_seconds)
            try:
                layer = await self.require_layer(account)
                if await layer.is_authorized():
                    client = await layer.authorized_client()
                    await client(functions.account.UpdateStatusRequest(offline=False))
                    self.online_status[account] = {
                        "account": account,
                        "keep_online": True,
                        "connected": client.is_connected(),
                        "last_update_ts": int(time.time()),
                        "interval_seconds": interval,
                    }
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.online_status[account] = {
                    "account": account,
                    "keep_online": True,
                    "error": str(exc),
                    "last_update_ts": int(time.time()),
                    "interval_seconds": interval,
                }
            await asyncio.sleep(interval)

    def start_reconnect_loop(self, account: str) -> None:
        account_name = self.resolve_account(account)
        task = self.reconnect_tasks.get(account_name)
        if task and not task.done():
            return
        self.reconnect_tasks[account_name] = asyncio.create_task(self._reconnect_loop(account_name))

    async def stop_reconnect_loop(self, account: str) -> None:
        account_name = self.resolve_account(account)
        task = self.reconnect_tasks.pop(account_name, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _reconnect_loop(self, account: str) -> None:
        delay = self.settings().service.reconnect_min_delay_seconds
        while True:
            service = self.settings().service
            min_delay = max(1, service.reconnect_min_delay_seconds)
            max_delay = max(min_delay, service.reconnect_max_delay_seconds)
            try:
                layer = await self.require_layer(account)
                client = await layer.authorized_client()
                if not client.is_connected():
                    await layer.connect()
                if await layer.is_authorized():
                    if service.keep_accounts_online:
                        self.start_online_keepalive(account)
                    if service.passive_update_receiver and account not in self.update_handlers:
                        await self.start_passive_update_receiver(account)
                    self.connection_health[account] = {
                        "account": account,
                        "ok": True,
                        "connected": client.is_connected(),
                        "last_check_ts": int(time.time()),
                    }
                delay = min_delay
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connection_health[account] = {
                    "account": account,
                    "ok": False,
                    "error": str(exc),
                    "last_check_ts": int(time.time()),
                    "next_retry_seconds": delay,
                }
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)
                continue
            await asyncio.sleep(max(min_delay, delay))

    async def start_passive_update_receiver(self, account: str) -> None:
        account_name = self.resolve_account(account)
        if account_name in self.update_handlers:
            return
        layer = await self.require_layer(account_name)
        if not await layer.is_authorized():
            return
        client = await layer.authorized_client()

        async def handler(event: Any) -> None:
            self.online_status.setdefault(account_name, {})
            self.online_status[account_name].update(
                {
                    "account": account_name,
                    "last_update_ts": int(time.time()),
                    "last_update_type": type(event).__name__,
                    "passive_receiver": True,
                }
            )

        builder = events.Raw()
        client.add_event_handler(handler, builder)
        self.update_handlers[account_name] = (handler, builder)

    async def stop_passive_update_receiver(self, account: str) -> None:
        account_name = self.resolve_account(account)
        handler_tuple = self.update_handlers.pop(account_name, None)
        layer = self.layers.get(account_name)
        if not handler_tuple or not layer:
            return
        try:
            client = await layer.authorized_client()
            handler, builder = handler_tuple
            client.remove_event_handler(handler, builder)
        except Exception:
            pass

    async def warm_entity_cache(self, account: str, *, limit: int) -> dict[str, Any]:
        account_name = self.resolve_account(account)
        layer = await self.require_layer(account_name)
        dialogs = await layer.get_dialogs(limit=limit)
        cache: dict[str, dict[str, Any]] = {}
        for dialog in dialogs:
            serialized = serialize_dialog(dialog)
            cache[str(serialized["id"])] = serialized
            username = serialized.get("username")
            if username:
                cache[f"@{username}".lower()] = serialized
                cache[str(username).lower()] = serialized
        self.entity_cache[account_name] = cache
        return {
            "account": account_name,
            "cached": len(cache),
            "dialog_limit": limit,
            "last_warmup_ts": int(time.time()),
        }

    async def check_connection_health(self, account: str | None = None) -> dict[str, Any]:
        account_name = self.resolve_account(account)
        timeout = self.settings().service.connection_health_timeout_seconds
        try:
            layer = await asyncio.wait_for(self.require_layer(account_name), timeout=timeout)
            connected = await asyncio.wait_for(layer.is_connected(), timeout=timeout)
            result = {
                "account": account_name,
                "ok": connected,
                "connected": connected,
                "last_check_ts": int(time.time()),
            }
        except Exception as exc:
            result = {
                "account": account_name,
                "ok": False,
                "error": str(exc),
                "last_check_ts": int(time.time()),
            }
        self.connection_health[account_name] = result
        if not result["ok"]:
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "Telegram connection health check failed; auth request blocked",
                    "health": result,
                },
            )
        return result


class ProxyPayload(BaseModel):
    proxy_url: str | None = None


class AccountPayload(BaseModel):
    account: str


class AccountConnectPayload(BaseModel):
    account: str | None = None
    keep_online: bool = True


class ClientProfilePayload(BaseModel):
    device_model: str = Field(default="Telegram Desktop", min_length=1)
    system_version: str = Field(default="Linux x86_64", min_length=1)
    app_version: str = Field(default=__version__, min_length=1)
    lang_code: str = Field(default="en", min_length=1)
    system_lang_code: str = Field(default="en-US", min_length=1)


class ServiceSettingsPayload(BaseModel):
    api_name: str = "tg-api-zapret"
    public_base_url: str | None = None
    default_api_interface: str = "rest"
    enabled_interfaces: list[str] = Field(
        default_factory=lambda: ["rest", "json_rpc", "websocket", "sse", "queue", "python_sdk"]
    )
    max_queue_jobs_list: int = Field(default=1000, ge=1)
    stream_queue_size: int = Field(default=100, ge=1)
    request_timeout_seconds: int = Field(default=60, ge=1)
    expose_docs: bool = False
    cors_origins: list[str] = Field(default_factory=list)
    require_api_token: bool = True
    api_token_env: str = "TG_API_TOKEN"
    api_tokens_env: str = "TG_API_TOKENS"
    rate_limit_per_minute: int = Field(default=120, ge=0)
    audit_log_path: str | None = None
    enable_raw_invoke: bool = False
    enable_layer_invoke: bool = False
    bot_token_accounts: dict[str, str] = Field(default_factory=dict)
    telegram_actions_per_minute: int = Field(default=20, ge=1)
    telegram_auth_requests_per_hour: int = Field(default=3, ge=1)
    max_dialog_limit: int = Field(default=100, ge=1)
    max_message_limit: int = Field(default=100, ge=1)
    blocked_account_names: list[str] = Field(default_factory=lambda: ["string", "account"])
    telegram_min_action_interval_seconds: float = Field(default=1.25, ge=0)
    queue_visibility_timeout_seconds: int = Field(default=300, ge=1)
    queue_default_max_attempts: int = Field(default=3, ge=1)
    keep_accounts_online: bool = True
    online_update_interval_seconds: int = Field(default=55, ge=15)
    auto_connect_accounts: list[str] = Field(default_factory=list)
    reconnect_enabled: bool = True
    reconnect_min_delay_seconds: int = Field(default=5, ge=1)
    reconnect_max_delay_seconds: int = Field(default=60, ge=1)
    passive_update_receiver: bool = True
    entity_cache_warmup_dialogs: int = Field(default=50, ge=0)
    require_connection_health_before_auth: bool = True
    connection_health_timeout_seconds: int = Field(default=20, ge=1)


class SendCodePayload(BaseModel):
    phone: str


class ConfirmCodePayload(BaseModel):
    phone: str
    phone_code_hash: str
    code: str


class PasswordPayload(BaseModel):
    password: str


class SendMessagePayload(BaseModel):
    entity: str | int
    text: str
    parse_mode: str | None = None


class SendUsernameMessagePayload(BaseModel):
    username: str = Field(description="Telegram username with or without @, phone, or t.me link.")
    text: str
    parse_mode: str | None = None


class EditMessagePayload(BaseModel):
    entity: str | int
    message_id: int
    text: str


class DeleteMessagesPayload(BaseModel):
    entity: str | int
    message_ids: list[int]
    revoke: bool = True


class ForwardMessagesPayload(BaseModel):
    from_entity: str | int
    to_entity: str | int
    message_ids: list[int]


class SendMediaPayload(BaseModel):
    entity: str | int
    file_path: str | None = None
    file_base64: str | None = None
    file_name: str | None = None
    caption: str | None = None
    parse_mode: str | None = None


class DownloadMediaPayload(BaseModel):
    entity: str | int
    message_id: int
    output_path: str | None = None
    as_base64: bool = True


class UploadFilePayload(BaseModel):
    file_path: str | None = None
    file_base64: str | None = None
    file_name: str | None = None


class EntityPayload(BaseModel):
    entity: str | int


class JoinLeavePayload(BaseModel):
    entity: str | int


class ReactionPayload(BaseModel):
    entity: str | int
    message_id: int
    reaction: str | dict[str, Any] | list[dict[str, Any]] | None = None
    big: bool | None = None
    add_to_recent: bool | None = None


class StoryGetPayload(BaseModel):
    entity: str | int
    story_ids: list[int]


class StorySendPayload(BaseModel):
    peer: str | int
    media: dict[str, Any]
    privacy_rules: list[dict[str, Any]]
    caption: str | None = None
    period: int | None = None
    pinned: bool | None = None
    noforwards: bool | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class AdminBanPayload(BaseModel):
    channel: str | int
    participant: str | int
    banned_rights: dict[str, Any] = Field(
        default_factory=lambda: {
            "_": "ChatBannedRights",
            "until_date": None,
            "view_messages": True,
        }
    )


class AdminPromotePayload(BaseModel):
    channel: str | int
    user: str | int
    admin_rights: dict[str, Any] = Field(default_factory=lambda: {"_": "ChatAdminRights"})
    rank: str | None = None


class TypeConstructorPayload(BaseModel):
    constructor: str = Field(description="TL type name, for example InputPeerUser or ReactionEmoji.")
    fields: dict[str, Any] = Field(default_factory=dict)


class RawInvokePayload(BaseModel):
    request: str = Field(
        description="Telethon TL function path, for example users.GetFullUserRequest"
    )
    kwargs: dict[str, Any] = Field(default_factory=dict)


class MtprotoLayerInvokePayload(BaseModel):
    request: str = Field(
        description="Layer function callable path, for example messages.SendMessageRequest"
    )
    kwargs: dict[str, Any] = Field(default_factory=dict)


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    id: str | int | None = None


class QueueJobPayload(BaseModel):
    kind: str
    account: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    max_attempts: int | None = Field(default=None, ge=1)


class ActionResolvePayload(BaseModel):
    task: str = Field(description="Natural task or known intent, for example send_message.")
    account: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    realtime: bool = False
    background: bool = False
    bidirectional: bool = False
    client_language: str | None = None


class ActionExecutePayload(ActionResolvePayload):
    pass


def create_app(state: ApiState) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            await state.startup()
            yield
        finally:
            await state.disconnect()

    app = FastAPI(title="tg-api-zapret", version=__version__, lifespan=lifespan)
    startup_service = state.settings().service
    if startup_service.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=startup_service.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        service = state.settings().service
        if not service.expose_docs and request.url.path in {"/docs", "/redoc", "/openapi.json"}:
            return JSONResponse({"detail": "Documentation is disabled"}, status_code=404)

        token = extract_bearer_token(request.headers.get("authorization"))
        scopes = token_scopes(service, token)
        if service.require_api_token and scopes is None and request.url.path != "/health":
            await audit_request(state, request, 401, token)
            return JSONResponse({"detail": "Missing or invalid API token"}, status_code=401)
        scope_token = REQUEST_SCOPES.set(scopes)

        rate_key = token_hash(token) if token else request.client.host if request.client else "unknown"
        if not check_rate_limit(state, rate_key, service.rate_limit_per_minute):
            await audit_request(state, request, 429, token)
            REQUEST_SCOPES.reset(scope_token)
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        account = request.query_params.get("account")
        if scopes is not None and account and not account_allowed(scopes, account):
            await audit_request(state, request, 403, token)
            REQUEST_SCOPES.reset(scope_token)
            return JSONResponse({"detail": "Account is not allowed for this token"}, status_code=403)
        if account:
            try:
                state.resolve_account(account)
            except ValueError as exc:
                await audit_request(state, request, 400, token)
                REQUEST_SCOPES.reset(scope_token)
                return JSONResponse({"detail": str(exc)}, status_code=400)

        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=service.request_timeout_seconds,
            )
            await audit_request(state, request, response.status_code, token)
            return response
        except TimeoutError:
            await audit_request(state, request, 504, token)
            return JSONResponse({"detail": "Request timeout"}, status_code=504)
        except FloodWaitError as exc:
            await audit_request(state, request, 429, token)
            return JSONResponse(
                {
                    "detail": "Telegram flood wait",
                    "seconds": getattr(exc, "seconds", None),
                    "retry_after": getattr(exc, "seconds", None),
                },
                status_code=429,
                headers={"Retry-After": str(getattr(exc, "seconds", 60))},
            )
        except RPCError as exc:
            await audit_request(state, request, 502, token)
            return JSONResponse(
                {
                    "detail": "Telegram RPC error",
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
                status_code=502,
            )
        except PermissionError as exc:
            await audit_request(state, request, 401, token)
            return JSONResponse({"detail": str(exc)}, status_code=401)
        except ValueError as exc:
            await audit_request(state, request, 400, token)
            return JSONResponse({"detail": str(exc)}, status_code=400)
        except ConnectionError as exc:
            await audit_request(state, request, 503, token)
            return JSONResponse(
                {"detail": "Telegram connection failed", "message": str(exc)},
                status_code=503,
            )
        finally:
            REQUEST_SCOPES.reset(scope_token)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/capabilities")
    async def capabilities() -> dict[str, Any]:
        return {
            "interfaces": {
                "rest": {
                    "description": "Simple request/response commands.",
                    "endpoints": [
                        "GET /dialogs",
                        "POST /accounts/connect",
                        "POST /accounts/disconnect",
                        "GET /accounts/online",
                        "GET /accounts/health",
                        "POST /accounts/entity-cache/warm",
                        "GET /accounts/entity-cache",
                        "POST /messages/send",
                        "POST /messages/send-username",
                        "POST /messages/edit",
                        "POST /messages/delete",
                        "POST /messages/forward",
                        "POST /messages/history/delete",
                        "POST /messages/reaction",
                        "POST /media/send",
                        "POST /media/download",
                        "POST /files/upload",
                        "POST /entities/resolve",
                        "POST /chats/join",
                        "POST /chats/leave",
                        "POST /stories/get",
                        "POST /stories/send",
                        "POST /admin/ban",
                        "POST /admin/promote",
                        "POST /tl/construct",
                        "POST /raw/invoke",
                        "GET /mtproto/layers/{layer}/functions",
                        "POST /mtproto/layers/{layer}/invoke",
                        "POST /bot{token}/{method}",
                    ],
                },
                "json_rpc": {
                    "description": "Single endpoint for command-style integrations.",
                    "endpoint": "POST /rpc",
                    "methods": sorted(RPC_METHODS),
                },
                "websocket": {
                    "description": "Bidirectional realtime updates.",
                    "endpoint": "WS /ws/updates",
                },
                "sse": {
                    "description": "One-way realtime event stream.",
                    "endpoint": "GET /events",
                },
                "queue": {
                    "description": "Background jobs. Backends: memory, redis. Redis jobs are executed by `tg-api-zapret worker`.",
                    "endpoints": ["POST /queue/jobs", "GET /queue/jobs/{job_id}"],
                },
                "python_sdk": {
                    "description": "Python client wrapper around HTTP/JSON-RPC/Queue APIs.",
                    "class": "tg_api_zapret.TgApiZapretClient",
                },
                "bot_api_compat": {
                    "description": "Limited Bot API compatibility layer, not a full Telegram Bot API proxy.",
                    "endpoint": "GET|POST /bot{token}/{method}",
                    "methods": sorted(BOT_API_COMPAT_METHODS),
                },
            },
            "service_settings": state.settings().service.to_dict(),
            "actions": ACTIONS,
        }

    @app.post("/actions/resolve")
    async def resolve_action(payload: ActionResolvePayload) -> dict[str, Any]:
        return resolve_api_method(payload, state.settings().service)

    @app.post("/actions/execute")
    async def execute_action(payload: ActionExecutePayload) -> dict[str, Any]:
        ensure_account_allowed_for_payload(state, payload.account)
        plan = resolve_api_method(payload, state.settings().service)
        if plan["interface"] == "queue":
            queue_payload = QueueJobPayload(
                kind=plan["rpc_method"],
                account=payload.account,
                payload=payload.params,
            )
            job_id = uuid4().hex
            job = await state.queue.create_job({
                "id": job_id,
                "kind": queue_payload.kind,
                "account": state.resolve_account(queue_payload.account),
                "payload": queue_payload.payload,
                "idempotency_key": queue_payload.idempotency_key,
                "attempts": 0,
                "max_attempts": queue_payload.max_attempts
                or state.settings().service.queue_default_max_attempts,
                "status": "queued",
                "result": None,
                "error": None,
            })
            if state.queue.runs_inline:
                asyncio.create_task(run_queue_job(state, job_id, queue_payload))
            return {"plan": plan, "job": job}
        if not plan.get("executable", False):
            return {"plan": plan, "status": "not_executable"}
        result = await dispatch_rpc(
            state,
            plan["rpc_method"],
            {"account": payload.account, **payload.params},
        )
        return {"plan": plan, "result": result}

    @app.websocket("/ws/updates")
    async def websocket_updates(websocket: WebSocket, account: str | None = None) -> None:
        await ensure_websocket_allowed(state, websocket, account)
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=state.settings().service.stream_queue_size
        )
        client = await require_authorized_client(state, account)

        async def handler(event: events.NewMessage.Event) -> None:
            await queue.put(
                {
                    "type": "new_message",
                    "account": state.resolve_account(account),
                    "message": serialize_message(event.message),
                }
            )

        client.add_event_handler(handler, events.NewMessage())
        try:
            while True:
                await websocket.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        finally:
            client.remove_event_handler(handler, events.NewMessage())

    @app.get("/events")
    async def sse_events(account: str | None = None) -> StreamingResponse:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=state.settings().service.stream_queue_size
        )
        client = await require_authorized_client(state, account)

        async def handler(event: events.NewMessage.Event) -> None:
            await queue.put(
                {
                    "type": "new_message",
                    "account": state.resolve_account(account),
                    "message": serialize_message(event.message),
                }
            )

        async def stream():
            client.add_event_handler(handler, events.NewMessage())
            try:
                while True:
                    event = await queue.get()
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            finally:
                client.remove_event_handler(handler, events.NewMessage())

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.get("/config")
    async def get_config() -> dict[str, Any]:
        settings = state.settings()
        return {
            "proxy_url": mask_url_secret(settings.proxy_url),
            "client_profile": settings.client_profile.to_dict(),
            "service": settings.service.to_dict(),
            "active_account": settings.active_account,
            "accounts": settings.accounts,
        }

    @app.get("/app/settings")
    async def get_app_settings() -> dict[str, Any]:
        return state.settings().service.to_dict()

    @app.put("/app/settings")
    async def set_app_settings(payload: ServiceSettingsPayload) -> dict[str, Any]:
        service = ServiceSettings.from_dict(payload.model_dump())
        settings = state.settings()
        state.save_settings(replace(settings, service=service))
        return service.to_dict()

    @app.patch("/app/settings")
    async def patch_app_settings(payload: dict[str, Any]) -> dict[str, Any]:
        current = state.settings()
        merged = {**current.service.to_dict(), **payload}
        service = ServiceSettings.from_dict(merged)
        state.save_settings(replace(current, service=service))
        return service.to_dict()

    @app.get("/accounts")
    async def accounts() -> dict[str, Any]:
        settings = state.settings()
        return visible_accounts_response(settings, REQUEST_SCOPES.get())

    @app.post("/accounts")
    async def add_account(payload: AccountPayload) -> dict[str, Any]:
        ensure_safe_account_payload(state, payload.account)
        settings = state.settings().with_account(payload.account)
        state.save_settings(settings)
        return {"active_account": settings.active_account, "accounts": settings.accounts}

    @app.post("/accounts/connect")
    async def connect_account(payload: AccountConnectPayload) -> dict[str, Any]:
        account_name = state.resolve_account(payload.account)
        layer = await state.require_layer(account_name)
        authorized = await layer.is_authorized()
        if payload.keep_online and authorized:
            await state.activate_desktop_like_runtime(account_name)
        return {
            "account": account_name,
            "connected": True,
            "authorized": authorized,
            "keep_online": payload.keep_online and authorized,
            "online_status": state.online_status.get(account_name),
        }

    @app.post("/accounts/disconnect")
    async def disconnect_account(payload: AccountConnectPayload) -> dict[str, Any]:
        account_name = state.resolve_account(payload.account)
        await state.disconnect(account_name)
        return {"account": account_name, "connected": False, "keep_online": False}

    @app.get("/accounts/online")
    async def online_accounts() -> dict[str, Any]:
        return {
            "keep_accounts_online": state.settings().service.keep_accounts_online,
            "accounts": state.online_status,
            "connection_health": state.connection_health,
            "running_tasks": sorted(
                account for account, task in state.online_tasks.items() if not task.done()
            ),
            "reconnect_tasks": sorted(
                account for account, task in state.reconnect_tasks.items() if not task.done()
            ),
            "passive_receivers": sorted(state.update_handlers),
        }

    @app.get("/accounts/health")
    async def account_health(account: str | None = None) -> dict[str, Any]:
        if account is not None:
            return await state.check_connection_health(account)
        results: dict[str, Any] = {}
        for account_name in state.settings().accounts:
            try:
                results[account_name] = await state.check_connection_health(account_name)
            except HTTPException as exc:
                results[account_name] = {
                    "account": account_name,
                    "ok": False,
                    "status_code": exc.status_code,
                    "error": exc.detail,
                }
        return {"accounts": results}

    @app.post("/accounts/entity-cache/warm")
    async def warm_account_entity_cache(
        account: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        limit = clamp_limit(limit, state.settings().service.max_dialog_limit)
        return await state.warm_entity_cache(state.resolve_account(account), limit=limit)

    @app.get("/accounts/entity-cache")
    async def account_entity_cache(account: str | None = None) -> dict[str, Any]:
        account_name = state.resolve_account(account)
        entities = state.entity_cache.get(account_name, {})
        return {
            "account": account_name,
            "count": len(entities),
            "entities": entities,
        }

    @app.put("/config/proxy")
    async def set_proxy(payload: ProxyPayload) -> dict[str, Any]:
        if payload.proxy_url:
            validate_proxy_url(payload.proxy_url)
        settings = state.settings()
        state.save_settings(replace(settings, proxy_url=payload.proxy_url))
        await reconnect(state)
        return {"proxy_url": mask_url_secret(payload.proxy_url)}

    @app.put("/config/client-profile")
    async def set_client_profile(payload: ClientProfilePayload) -> dict[str, Any]:
        settings = state.settings()
        profile = ClientProfile(**payload.model_dump())
        state.save_settings(replace(settings, client_profile=profile))
        await reconnect(state)
        return {"client_profile": profile.to_dict()}

    @app.get("/auth/status")
    async def auth_status(account: str | None = None) -> dict[str, Any]:
        layer = await state.require_layer(account)
        return {"account": state.resolve_account(account), "authorized": await layer.is_authorized()}

    @app.post("/auth/send-code")
    async def send_code(payload: SendCodePayload, account: str | None = None) -> dict[str, str]:
        ensure_telegram_auth_rate(state, account)
        if state.settings().service.require_connection_health_before_auth:
            await state.check_connection_health(state.resolve_account(account))
        layer = await state.require_layer(account)
        sent = await layer.send_code(payload.phone)
        return {
            "account": state.resolve_account(account),
            "phone": sent.phone,
            "phone_code_hash": sent.phone_code_hash,
        }

    @app.post("/auth/confirm-code")
    async def confirm_code(payload: ConfirmCodePayload, account: str | None = None) -> dict[str, str]:
        ensure_telegram_auth_rate(state, account)
        layer = await state.require_layer(account)
        try:
            await layer.sign_in(
                SentCode(phone=payload.phone, phone_code_hash=payload.phone_code_hash),
                payload.code,
            )
        except SessionPasswordNeededError:
            return {"status": "password_required"}
        await state.activate_desktop_like_runtime(state.resolve_account(account))
        return {"status": "authorized"}

    @app.post("/auth/password")
    async def confirm_password(payload: PasswordPayload, account: str | None = None) -> dict[str, str]:
        ensure_telegram_auth_rate(state, account)
        layer = await state.require_layer(account)
        try:
            await layer.sign_in_password(payload.password)
        except PasswordHashInvalidError as exc:
            raise HTTPException(status_code=400, detail="Invalid two-step password") from exc
        await state.activate_desktop_like_runtime(state.resolve_account(account))
        return {"status": "authorized"}

    @app.get("/me")
    async def me(account: str | None = None) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "me")
        client = await require_authorized_client(state, account)
        return serialize_user(await client.get_me())

    @app.get("/dialogs")
    async def dialogs(limit: int = 20, account: str | None = None) -> list[dict[str, Any]]:
        ensure_telegram_rate(state, account, "dialogs")
        limit = clamp_limit(limit, state.settings().service.max_dialog_limit)
        layer = await state.require_layer(account)
        return [serialize_dialog(dialog) for dialog in await layer.get_dialogs(limit=limit)]

    @app.get("/messages/{entity}")
    async def messages(
        entity: str,
        limit: int = 50,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        ensure_telegram_rate(state, account, "messages")
        limit = clamp_limit(limit, state.settings().service.max_message_limit)
        layer = await state.require_layer(account)
        return [serialize_message(message) async for message in layer.iter_messages(entity, limit=limit)]

    @app.post("/messages/send")
    async def send_message(
        payload: SendMessagePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.send")
        layer = await state.require_layer(account)
        message = await layer.send_message(
            payload.entity,
            payload.text,
            parse_mode=payload.parse_mode,
        )
        return serialize_message(message)

    @app.post("/messages/send-username")
    async def send_username_message(
        payload: SendUsernameMessagePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.send")
        layer = await state.require_layer(account)
        message = await layer.send_message(
            normalize_username_entity(payload.username),
            payload.text,
            parse_mode=payload.parse_mode,
        )
        return serialize_message(message)

    @app.post("/messages/edit")
    async def edit_message(
        payload: EditMessagePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.edit")
        client = await require_authorized_client(state, account)
        message = await client.edit_message(payload.entity, payload.message_id, payload.text)
        return serialize_message(message)

    @app.post("/messages/delete")
    async def delete_messages(
        payload: DeleteMessagesPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.delete")
        client = await require_authorized_client(state, account)
        result = await client.delete_messages(
            payload.entity,
            payload.message_ids,
            revoke=payload.revoke,
        )
        return {"result": str(result)}

    @app.post("/messages/forward")
    async def forward_messages(
        payload: ForwardMessagesPayload,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        ensure_telegram_rate(state, account, "messages.forward")
        client = await require_authorized_client(state, account)
        result = await client.forward_messages(
            payload.to_entity,
            payload.message_ids,
            from_peer=payload.from_entity,
        )
        messages = result if isinstance(result, list) else [result]
        return [serialize_message(message) for message in messages]

    @app.post("/messages/history/delete")
    async def delete_history(
        payload: EntityPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.history.delete")
        client = await require_authorized_client(state, account)
        peer = await resolve_entity(payload.entity, client=client)
        result = await client(functions.messages.DeleteHistoryRequest(peer=peer, max_id=0))
        return {"result": serialize_tl(result)}

    @app.post("/messages/reaction")
    async def send_reaction(
        payload: ReactionPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "messages.reaction")
        client = await require_authorized_client(state, account)
        peer = await resolve_entity(payload.entity, client=client)
        reaction = await build_reaction(payload.reaction, client)
        result = await client(
            functions.messages.SendReactionRequest(
                peer=peer,
                msg_id=payload.message_id,
                big=payload.big,
                add_to_recent=payload.add_to_recent,
                reaction=reaction,
            )
        )
        return {"result": serialize_tl(result)}

    @app.post("/media/send")
    async def send_media(
        payload: SendMediaPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "media.send")
        client = await require_authorized_client(state, account)
        file_value, cleanup = decode_upload_file(payload.file_path, payload.file_base64, payload.file_name)
        try:
            message = await client.send_file(
                payload.entity,
                file_value,
                caption=payload.caption,
                parse_mode=payload.parse_mode,
            )
        finally:
            if cleanup:
                Path(cleanup).unlink(missing_ok=True)
        return serialize_message(message)

    @app.post("/media/download")
    async def download_media(
        payload: DownloadMediaPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "media.download")
        client = await require_authorized_client(state, account)
        message = await client.get_messages(payload.entity, ids=payload.message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        if payload.output_path:
            output = await client.download_media(message, file=payload.output_path)
            return {"path": str(output) if output else None}
        data = await client.download_media(message, file=bytes)
        if data is None:
            return {"data": None}
        if payload.as_base64:
            return {
                "data": {"_": "bytes", "base64": base64.b64encode(data).decode("ascii")}
            }
        return {"data": data.decode("utf-8", errors="replace")}

    @app.post("/files/upload")
    async def upload_file(
        payload: UploadFilePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "files.upload")
        client = await require_authorized_client(state, account)
        file_value, cleanup = decode_upload_file(payload.file_path, payload.file_base64, payload.file_name)
        try:
            uploaded = await client.upload_file(file_value)
        finally:
            if cleanup:
                Path(cleanup).unlink(missing_ok=True)
        return {"file": serialize_tl(uploaded)}

    @app.post("/entities/resolve")
    async def resolve_entity_endpoint(
        payload: EntityPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "entities.resolve")
        client = await require_authorized_client(state, account)
        entity = await client.get_entity(payload.entity)
        input_entity = await resolve_entity(payload.entity, client=client)
        return {"entity": serialize_tl(entity), "input_entity": serialize_tl(input_entity)}

    @app.post("/chats/join")
    async def join_chat(
        payload: JoinLeavePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "chats.join")
        client = await require_authorized_client(state, account)
        request = await build_tl_request(
            "channels.JoinChannelRequest",
            {"channel": payload.entity},
            client,
        )
        result = await client(request)
        return {"result": serialize_tl(result)}

    @app.post("/chats/leave")
    async def leave_chat(
        payload: JoinLeavePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "chats.leave")
        client = await require_authorized_client(state, account)
        request = await build_tl_request(
            "channels.LeaveChannelRequest",
            {"channel": payload.entity},
            client,
        )
        result = await client(request)
        return {"result": serialize_tl(result)}

    @app.post("/stories/get")
    async def get_stories(
        payload: StoryGetPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "stories.get")
        client = await require_authorized_client(state, account)
        peer = await resolve_entity(payload.entity, client=client)
        result = await client(functions.stories.GetStoriesByIDRequest(peer=peer, id=payload.story_ids))
        return {"result": serialize_tl(result)}

    @app.post("/stories/send")
    async def send_story(
        payload: StorySendPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "stories.send")
        client = await require_authorized_client(state, account)
        kwargs = {
            "peer": payload.peer,
            "media": payload.media,
            "privacy_rules": payload.privacy_rules,
            "caption": payload.caption,
            "period": payload.period,
            "pinned": payload.pinned,
            "noforwards": payload.noforwards,
            **payload.extra,
        }
        request = await build_tl_request(
            "stories.SendStoryRequest",
            {key: value for key, value in kwargs.items() if value is not None},
            client,
        )
        result = await client(request)
        return {"result": serialize_tl(result)}

    @app.post("/admin/ban")
    async def admin_ban(
        payload: AdminBanPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "admin.ban")
        client = await require_authorized_client(state, account)
        request = await build_tl_request(
            "channels.EditBannedRequest",
            {
                "channel": payload.channel,
                "participant": payload.participant,
                "banned_rights": payload.banned_rights,
            },
            client,
        )
        result = await client(request)
        return {"result": serialize_tl(result)}

    @app.post("/admin/promote")
    async def admin_promote(
        payload: AdminPromotePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_telegram_rate(state, account, "admin.promote")
        client = await require_authorized_client(state, account)
        request = await build_tl_request(
            "channels.EditAdminRequest",
            {
                "channel": payload.channel,
                "user_id": payload.user,
                "admin_rights": payload.admin_rights,
                "rank": payload.rank,
            },
            client,
        )
        result = await client(request)
        return {"result": serialize_tl(result)}

    @app.post("/tl/construct")
    async def construct_tl_object(
        payload: TypeConstructorPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        layer = await state.require_layer(account)
        client = await layer.authorized_client() if await layer.is_authorized() else None
        result = await build_tl_object(payload.constructor, payload.fields, client)
        return {"type": type(result).__name__, "object": serialize_tl(result)}

    @app.post("/raw/invoke")
    async def raw_invoke(payload: RawInvokePayload, account: str | None = None) -> dict[str, Any]:
        ensure_raw_enabled(state)
        ensure_telegram_rate(state, account, "raw.invoke")
        layer = await state.require_layer(account)
        client = await layer.authorized_client()
        request = await build_tl_request(payload.request, payload.kwargs, client)
        result = await layer.invoke(request)
        return {"type": type(result).__name__, "result": serialize_tl(result)}

    @app.get("/mtproto/layers/{layer}/functions")
    async def mtproto_layer_functions(layer: int) -> dict[str, Any]:
        try:
            functions = get_layer_functions(layer)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"layer": layer, "function_count": len(functions), "functions": functions}

    @app.post("/mtproto/layers/{layer}/invoke")
    async def mtproto_layer_invoke(
        layer: int,
        payload: MtprotoLayerInvokePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        ensure_layer_enabled(state)
        ensure_telegram_rate(state, account, "layer.invoke")
        try:
            require_layer_function(layer, payload.request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        telegram_layer = await state.require_layer(account)
        client = await telegram_layer.authorized_client()
        request = await build_tl_request(payload.request, payload.kwargs, client)
        result = await telegram_layer.invoke(request)
        return {
            "layer": layer,
            "request": payload.request,
            "type": type(result).__name__,
            "result": serialize_tl(result),
        }

    @app.post("/rpc")
    async def json_rpc(payload: JsonRpcRequest) -> dict[str, Any]:
        try:
            result = await dispatch_rpc(state, payload.method, payload.params)
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": payload.id,
                "error": {"code": -32000, "message": str(exc)},
            }
        return {"jsonrpc": "2.0", "id": payload.id, "result": result}

    @app.post("/queue/jobs")
    async def enqueue_job(payload: QueueJobPayload) -> dict[str, Any]:
        ensure_account_allowed_for_payload(state, payload.account)
        job_id = uuid4().hex
        job = await state.queue.create_job({
            "id": job_id,
            "kind": payload.kind,
            "account": state.resolve_account(payload.account),
            "payload": payload.payload,
            "idempotency_key": payload.idempotency_key,
            "attempts": 0,
            "max_attempts": payload.max_attempts
            or state.settings().service.queue_default_max_attempts,
            "status": "queued",
            "result": None,
            "error": None,
        })
        if state.queue.runs_inline:
            asyncio.create_task(run_queue_job(state, job_id, payload))
        return job

    @app.get("/queue/jobs")
    async def list_jobs() -> list[dict[str, Any]]:
        return await state.queue.list_jobs()

    @app.get("/queue/jobs/{job_id}")
    async def get_job(job_id: str) -> dict[str, Any]:
        job = await state.queue.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @app.get("/compat/reverse-proxy")
    async def reverse_proxy_compat() -> dict[str, Any]:
        base_url = state.settings().service.public_base_url or "http://127.0.0.1:8080"
        return {
            "bot_api_base_url": f"{base_url.rstrip('/')}/bot<TOKEN>",
            "dns_override": "Point api.telegram.org to this service only for apps that use Bot API HTTPS.",
            "nginx_location": (
                "location /bot { proxy_pass http://127.0.0.1:8080; "
                "proxy_set_header Host $host; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }"
            ),
            "limits": [
                "MTProto client libraries cannot be transparently replaced by DNS; use SDK/adapters.",
                "Official Telegram apps cannot be forced through this API without changing their code/proxy.",
            ],
        }

    @app.get("/bot{token}/{method}", operation_id="bot_api_compat_get")
    async def bot_api_compat_get(token: str, method: str, request: Request) -> JSONResponse:
        return await handle_bot_api_compat(state, token, method, request)

    @app.post("/bot{token}/{method}", operation_id="bot_api_compat_post")
    async def bot_api_compat_post(token: str, method: str, request: Request) -> JSONResponse:
        return await handle_bot_api_compat(state, token, method, request)

    return app


async def handle_bot_api_compat(
    state: ApiState,
    token: str,
    method: str,
    request: Request,
) -> JSONResponse:
    account = resolve_bot_account(state, token)
    try:
        ensure_account_allowed_for_payload(state, account)
        params = await read_bot_api_params(request)
        result = await dispatch_bot_api(state, account, token, method, params)
    except HTTPException as exc:
        return JSONResponse(
            {"ok": False, "error_code": exc.status_code, "description": exc.detail},
            status_code=exc.status_code,
        )
    except Exception as exc:
        return JSONResponse(
            {"ok": False, "error_code": 500, "description": str(exc)},
            status_code=500,
        )
    return JSONResponse({"ok": True, "result": result})


async def reconnect(state: ApiState) -> None:
    await state.disconnect()


def decode_upload_file(
    file_path: str | None,
    file_base64: str | None,
    file_name: str | None,
) -> tuple[str | bytes, str | None]:
    if file_path:
        return file_path, None
    if not file_base64:
        raise HTTPException(status_code=400, detail="file_path or file_base64 is required")
    data = base64.b64decode(file_base64)
    if not file_name:
        return data, None
    suffix = Path(file_name).suffix
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(data)
        return handle.name, handle.name
    finally:
        handle.close()


async def build_reaction(value: Any, client: Any) -> list[Any] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [types.ReactionEmoji(emoticon=value)]
    if isinstance(value, list):
        return [await build_tl_object(str(item.get("_", "ReactionEmoji")), item, client) for item in value]
    if isinstance(value, dict):
        return [await build_tl_object(str(value.get("_", "ReactionEmoji")), value, client)]
    raise HTTPException(status_code=400, detail="Unsupported reaction payload")


async def read_bot_api_params(request: Request) -> dict[str, Any]:
    params: dict[str, Any] = dict(request.query_params)
    if request.method != "POST":
        return params
    body = await request.body()
    if not body:
        return params
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        loaded = json.loads(body.decode("utf-8"))
        if isinstance(loaded, dict):
            params.update(loaded)
        return params
    from urllib.parse import parse_qs

    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    params.update({key: values[-1] if len(values) == 1 else values for key, values in parsed.items()})
    return params


def resolve_bot_account(state: ApiState, token: str) -> str:
    service = state.settings().service
    return normalize_account_name(service.bot_token_accounts.get(token) or state.settings().active_account)


async def dispatch_bot_api(
    state: ApiState,
    account: str,
    token: str,
    method: str,
    params: dict[str, Any],
) -> Any:
    normalized = method.lower()
    client = await require_authorized_client(state, account)
    if normalized == "getme":
        ensure_telegram_rate(state, account, "bot.getme")
        return bot_user(await client.get_me())
    if normalized == "sendmessage":
        ensure_telegram_rate(state, account, "bot.sendmessage")
        chat_id = required_param(params, "chat_id")
        text = required_param(params, "text")
        message = await client.send_message(chat_id, text, parse_mode=params.get("parse_mode"))
        return bot_message(message)
    if normalized in {"sendphoto", "senddocument"}:
        ensure_telegram_rate(state, account, f"bot.{normalized}")
        chat_id = required_param(params, "chat_id")
        file_value = required_param(params, "photo" if normalized == "sendphoto" else "document")
        message = await client.send_file(chat_id, file_value, caption=params.get("caption"))
        return bot_message(message)
    if normalized == "editmessagetext":
        ensure_telegram_rate(state, account, "bot.editmessagetext")
        chat_id = required_param(params, "chat_id")
        message_id = int(required_param(params, "message_id"))
        message = await client.edit_message(chat_id, message_id, required_param(params, "text"))
        return bot_message(message)
    if normalized == "deletemessage":
        ensure_telegram_rate(state, account, "bot.deletemessage")
        chat_id = required_param(params, "chat_id")
        message_id = int(required_param(params, "message_id"))
        await client.delete_messages(chat_id, [message_id], revoke=True)
        return True
    if normalized == "getupdates":
        ensure_telegram_rate(state, account, "bot.getupdates")
        await ensure_bot_update_handler(state, token, account)
        offset = int(params.get("offset") or 0)
        limit = int(params.get("limit") or 100)
        updates = [
            update for update in state.bot_updates.get(token, []) if update["update_id"] >= offset
        ][:limit]
        return updates
    raise HTTPException(
        status_code=404,
        detail={
            "message": f"Unsupported Bot API compatibility method: {method}",
            "supported_methods": sorted(BOT_API_COMPAT_METHODS),
        },
    )


async def ensure_bot_update_handler(state: ApiState, token: str, account: str) -> None:
    key = f"{token}:{account}"
    if key in state.bot_update_handlers:
        return
    client = await require_authorized_client(state, account)
    state.bot_updates.setdefault(token, [])
    state.bot_update_ids.setdefault(token, 0)

    async def handler(event: events.NewMessage.Event) -> None:
        state.bot_update_ids[token] += 1
        state.bot_updates[token].append(
            {
                "update_id": state.bot_update_ids[token],
                "message": bot_message(event.message),
            }
        )
        max_updates = state.settings().service.max_queue_jobs_list
        state.bot_updates[token] = state.bot_updates[token][-max_updates:]

    builder = events.NewMessage()
    client.add_event_handler(handler, builder)
    state.bot_update_handlers[key] = (handler, builder)


def required_param(params: dict[str, Any], name: str) -> Any:
    value = params.get(name)
    if value is None or value == "":
        raise HTTPException(status_code=400, detail=f"{name} is required")
    return value


def bot_user(user: User | None) -> dict[str, Any]:
    data = serialize_user(user)
    data["is_bot"] = bool(user.bot) if user else False
    return data


def bot_message(message: Message) -> dict[str, Any]:
    return {
        "message_id": message.id,
        "date": int(message.date.timestamp()) if message.date else None,
        "chat": {"id": message.chat_id, "type": "private" if message.is_private else "group"},
        "from": {"id": message.sender_id} if message.sender_id else None,
        "text": message.message,
        "caption": getattr(message, "text", None) if message.media else None,
    }


def extract_bearer_token(header: str | None) -> str | None:
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def token_scopes(service: ServiceSettings, token: str | None) -> list[str] | None:
    if not token:
        return None
    tokens_json = os.getenv(service.api_tokens_env)
    if tokens_json:
        try:
            tokens = json.loads(tokens_json)
        except json.JSONDecodeError:
            tokens = {}
        scopes = tokens.get(token)
        if isinstance(scopes, list):
            return [str(scope) for scope in scopes]
    single_token = os.getenv(service.api_token_env)
    if single_token and token == single_token:
        return ["*"]
    return None


def check_rate_limit(state: ApiState, key: str, limit_per_minute: int) -> bool:
    if limit_per_minute <= 0:
        return True
    now = time.time()
    window_start = now - 60
    timestamps = [item for item in state.rate_limits.get(key, []) if item >= window_start]
    if len(timestamps) >= limit_per_minute:
        state.rate_limits[key] = timestamps
        return False
    timestamps.append(now)
    state.rate_limits[key] = timestamps
    return True


def ensure_telegram_rate(state: ApiState, account: str | None, action: str) -> None:
    service = state.settings().service
    account_name = state.resolve_account(account)
    now = time.monotonic()
    previous = state.last_telegram_action_at.get(account_name)
    min_interval = service.telegram_min_action_interval_seconds
    if previous is not None and min_interval > 0:
        wait_for = min_interval - (now - previous)
        if wait_for > 0:
            retry_after = max(1, int(wait_for + 0.999))
            raise HTTPException(
                status_code=429,
                detail=(
                    "Telegram desktop-like pacing is active for this account. "
                    f"Retry after {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )
    key = f"{account_name}:{action}"
    if not check_bucket(
        state.telegram_rate_limits,
        key,
        service.telegram_actions_per_minute,
        window_seconds=60,
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Telegram action rate limit exceeded for this account/action. "
                f"Limit: {service.telegram_actions_per_minute}/minute."
            ),
            headers={"Retry-After": "60"},
        )
    state.last_telegram_action_at[account_name] = now


def ensure_telegram_auth_rate(state: ApiState, account: str | None) -> None:
    service = state.settings().service
    account_name = state.resolve_account(account)
    if not check_bucket(
        state.telegram_auth_rate_limits,
        account_name,
        service.telegram_auth_requests_per_hour,
        window_seconds=3600,
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Telegram auth rate limit exceeded for this account. "
                f"Limit: {service.telegram_auth_requests_per_hour}/hour."
            ),
            headers={"Retry-After": "3600"},
        )


def check_bucket(
    buckets: dict[str, list[float]],
    key: str,
    limit: int,
    *,
    window_seconds: int,
) -> bool:
    now = time.time()
    window_start = now - window_seconds
    timestamps = [item for item in buckets.get(key, []) if item >= window_start]
    if len(timestamps) >= limit:
        buckets[key] = timestamps
        return False
    timestamps.append(now)
    buckets[key] = timestamps
    return True


def clamp_limit(limit: int, maximum: int) -> int:
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    return min(limit, maximum)


def ensure_safe_account_payload(state: ApiState, account: str) -> None:
    state.resolve_account(account)


async def audit_request(
    state: ApiState,
    request: Request,
    status_code: int,
    token: str | None,
) -> None:
    path = state.settings().service.audit_log_path
    if not path:
        return
    audit_path = Path(path).expanduser()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "client": request.client.host if request.client else None,
        "account": request.query_params.get("account"),
        "token": token_hash(token) if token else None,
    }
    with audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def token_hash(token: str | None) -> str:
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def account_allowed(scopes: list[str], account: str | None) -> bool:
    if not account or "*" in scopes:
        return True
    return normalize_account_name(account) in {normalize_account_name(scope) for scope in scopes}


def ensure_account_allowed_for_payload(state: ApiState, account: str | None) -> None:
    scopes = REQUEST_SCOPES.get()
    if scopes is not None and not account_allowed(scopes, account or state.settings().active_account):
        raise HTTPException(status_code=403, detail="Account is not allowed for this token")


async def ensure_websocket_allowed(
    state: ApiState,
    websocket: WebSocket,
    account: str | None,
) -> None:
    service = state.settings().service
    token = websocket.query_params.get("token") or extract_bearer_token(
        websocket.headers.get("authorization")
    )
    scopes = token_scopes(service, token)
    if service.require_api_token and scopes is None:
        await websocket.close(code=1008, reason="Missing or invalid API token")
        raise WebSocketDisconnect
    if scopes is not None and not account_allowed(scopes, account or state.settings().active_account):
        await websocket.close(code=1008, reason="Account is not allowed for this token")
        raise WebSocketDisconnect


def ensure_raw_enabled(state: ApiState) -> None:
    if not state.settings().service.enable_raw_invoke:
        raise HTTPException(status_code=403, detail="Raw invoke is disabled")


def ensure_layer_enabled(state: ApiState) -> None:
    if not state.settings().service.enable_layer_invoke:
        raise HTTPException(status_code=403, detail="Layer invoke is disabled")


def mask_url_secret(url: str | None) -> str | None:
    if not url or "@" not in url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    auth, address = rest.rsplit("@", 1)
    username = auth.split(":", 1)[0]
    return f"{scheme}://{username}:***@{address}"


def normalize_username_entity(value: str) -> str:
    entity = value.strip()
    if not entity:
        raise HTTPException(status_code=400, detail="username is required")
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if entity.startswith(prefix):
            entity = entity.removeprefix(prefix).split("?", 1)[0].strip("/")
            break
    if entity.startswith("+") or entity.startswith("@") or entity.lstrip("-").isdigit():
        return entity
    if "/" in entity:
        return entity
    return f"@{entity}"


def visible_accounts_response(settings: AppSettings, scopes: list[str] | None) -> dict[str, Any]:
    if scopes is None or "*" in scopes:
        return {"active_account": settings.active_account, "accounts": settings.accounts}
    allowed = {normalize_account_name(scope) for scope in scopes}
    accounts = [account for account in settings.accounts if account in allowed]
    active = settings.active_account if settings.active_account in accounts else accounts[0] if accounts else None
    return {"active_account": active, "accounts": accounts}


async def require_authorized_client(state: ApiState, account: str | None = None):
    layer = await state.require_layer(account)
    return await layer._require_authorized_client()


async def dispatch_rpc(state: ApiState, method: str, params: dict[str, Any]) -> Any:
    account = params.pop("account", None)
    ensure_account_allowed_for_payload(state, account)
    if method == "accounts.list":
        settings = state.settings()
        return visible_accounts_response(settings, REQUEST_SCOPES.get())
    if method == "auth.status":
        layer = await state.require_layer(account)
        return {"account": state.resolve_account(account), "authorized": await layer.is_authorized()}
    if method == "dialogs.list":
        ensure_telegram_rate(state, account, "dialogs")
        limit = clamp_limit(int(params.get("limit", 20)), state.settings().service.max_dialog_limit)
        layer = await state.require_layer(account)
        return [
            serialize_dialog(dialog)
            for dialog in await layer.get_dialogs(limit=limit)
        ]
    if method == "messages.send":
        ensure_telegram_rate(state, account, "messages.send")
        layer = await state.require_layer(account)
        message = await layer.send_message(
            params["entity"],
            params["text"],
            parse_mode=params.get("parse_mode"),
        )
        return serialize_message(message)
    if method == "messages.send_username":
        ensure_telegram_rate(state, account, "messages.send")
        layer = await state.require_layer(account)
        message = await layer.send_message(
            normalize_username_entity(params["username"]),
            params["text"],
            parse_mode=params.get("parse_mode"),
        )
        return serialize_message(message)
    if method == "messages.edit":
        ensure_telegram_rate(state, account, "messages.edit")
        client = await require_authorized_client(state, account)
        message = await client.edit_message(params["entity"], int(params["message_id"]), params["text"])
        return serialize_message(message)
    if method == "messages.delete":
        ensure_telegram_rate(state, account, "messages.delete")
        client = await require_authorized_client(state, account)
        result = await client.delete_messages(
            params["entity"],
            list(params["message_ids"]),
            revoke=bool(params.get("revoke", True)),
        )
        return {"result": serialize_tl(result)}
    if method == "messages.forward":
        ensure_telegram_rate(state, account, "messages.forward")
        client = await require_authorized_client(state, account)
        result = await client.forward_messages(
            params["to_entity"],
            list(params["message_ids"]),
            from_peer=params["from_entity"],
        )
        messages = result if isinstance(result, list) else [result]
        return [serialize_message(message) for message in messages]
    if method == "entities.resolve":
        ensure_telegram_rate(state, account, "entities.resolve")
        client = await require_authorized_client(state, account)
        entity = await client.get_entity(params["entity"])
        input_entity = await resolve_entity(params["entity"], client=client)
        return {"entity": serialize_tl(entity), "input_entity": serialize_tl(input_entity)}
    if method == "media.send":
        ensure_telegram_rate(state, account, "media.send")
        client = await require_authorized_client(state, account)
        file_value, cleanup = decode_upload_file(
            params.get("file_path"),
            params.get("file_base64"),
            params.get("file_name"),
        )
        try:
            message = await client.send_file(
                params["entity"],
                file_value,
                caption=params.get("caption"),
                parse_mode=params.get("parse_mode"),
            )
        finally:
            if cleanup:
                Path(cleanup).unlink(missing_ok=True)
        return serialize_message(message)
    if method == "tl.construct":
        layer = await state.require_layer(account)
        client = await layer.authorized_client() if await layer.is_authorized() else None
        result = await build_tl_object(params["constructor"], params.get("fields", {}), client)
        return {"type": type(result).__name__, "object": serialize_tl(result)}
    if method == "raw.invoke":
        ensure_raw_enabled(state)
        ensure_telegram_rate(state, account, "raw.invoke")
        layer = await state.require_layer(account)
        client = await layer.authorized_client()
        request = await build_tl_request(params["request"], params.get("kwargs", {}), client)
        result = await layer.invoke(request)
        return {"type": type(result).__name__, "result": serialize_tl(result)}
    raise ValueError(f"Unknown RPC method: {method}")


async def run_queue_job(state: ApiState, job_id: str, payload: QueueJobPayload) -> None:
    job = await state.queue.get_job(job_id)
    if job and job.get("status") == "queued":
        await state.queue.update_job(
            job_id,
            status="running",
            attempts=int(job.get("attempts") or 0) + 1,
        )
    else:
        await state.queue.update_job(job_id, status="running")
    try:
        result = await dispatch_rpc(
            state,
            payload.kind,
            {"account": payload.account, **payload.payload},
        )
        await state.queue.update_job(job_id, result=result, status="done")
    except Exception as exc:
        job = await state.queue.get_job(job_id)
        attempts = int((job or {}).get("attempts") or 0)
        max_attempts = int((job or {}).get("max_attempts") or 1)
        if attempts < max_attempts:
            await state.queue.requeue_job(job_id, error=str(exc))
        else:
            await state.queue.dead_letter_job(job_id, error=str(exc))


async def run_queue_worker(state: ApiState, *, poll_timeout: int = 5) -> None:
    while True:
        job = await state.queue.reserve_job(timeout=poll_timeout)
        if job is None:
            continue
        payload = QueueJobPayload(
            kind=job["kind"],
            account=job.get("account"),
            payload=job.get("payload") or {},
        )
        await run_queue_job(state, job["id"], payload)


RPC_METHODS = {
    "accounts.list",
    "auth.status",
    "dialogs.list",
    "entities.resolve",
    "media.send",
    "messages.delete",
    "messages.edit",
    "messages.forward",
    "messages.send",
    "messages.send_username",
    "raw.invoke",
    "tl.construct",
}


BOT_API_COMPAT_METHODS = {
    "deleteMessage",
    "editMessageText",
    "getMe",
    "getUpdates",
    "sendDocument",
    "sendMessage",
    "sendPhoto",
}


ACTIONS: dict[str, dict[str, Any]] = {
    "accounts": {
        "aliases": ["accounts", "list accounts", "аккаунты", "список аккаунтов"],
        "interface": "json_rpc",
        "rpc_method": "accounts.list",
        "rest": "GET /accounts",
        "executable": True,
    },
    "auth_status": {
        "aliases": ["auth status", "status", "статус", "проверить авторизацию"],
        "interface": "rest",
        "rpc_method": "auth.status",
        "rest": "GET /auth/status",
        "executable": True,
    },
    "list_dialogs": {
        "aliases": ["dialogs", "list dialogs", "chats", "диалоги", "чаты"],
        "interface": "rest",
        "rpc_method": "dialogs.list",
        "rest": "GET /dialogs",
        "executable": True,
    },
    "send_message": {
        "aliases": ["send message", "message send", "отправить сообщение", "сообщение"],
        "interface": "rest",
        "rpc_method": "messages.send",
        "rest": "POST /messages/send",
        "queue": "POST /queue/jobs kind=messages.send",
        "executable": True,
    },
    "stream_updates": {
        "aliases": ["updates", "stream updates", "new messages", "события", "новые сообщения"],
        "interface": "sse",
        "websocket": "WS /ws/updates",
        "sse": "GET /events",
        "executable": False,
    },
    "raw_invoke": {
        "aliases": ["raw", "invoke", "tl", "mtproto", "сырой вызов"],
        "interface": "json_rpc",
        "rpc_method": "raw.invoke",
        "rest": "POST /raw/invoke",
        "executable": True,
    },
}


def resolve_api_method(
    payload: ActionResolvePayload,
    service: ServiceSettings | None = None,
) -> dict[str, Any]:
    action_name = find_action(payload.task)
    action = ACTIONS[action_name]
    interface = choose_interface(payload, action, service or ServiceSettings())
    return {
        "action": action_name,
        "interface": interface,
        "endpoint": endpoint_for_interface(interface, action),
        "rpc_method": action.get("rpc_method"),
        "account": payload.account,
        "executable": action.get("executable", False),
        "reason": reason_for_interface(interface, payload),
        "params": payload.params,
    }


def find_action(task: str) -> str:
    normalized = task.strip().lower()
    for action_name, action in ACTIONS.items():
        if normalized == action_name or normalized in action["aliases"]:
            return action_name
    for action_name, action in ACTIONS.items():
        if any(alias in normalized for alias in action["aliases"]):
            return action_name
    return "raw_invoke"


def choose_interface(
    payload: ActionResolvePayload,
    action: dict[str, Any],
    service: ServiceSettings,
) -> str:
    language = (payload.client_language or "").lower()
    if language == "python":
        return first_enabled(["python_sdk", service.default_api_interface, "rest"], service)
    if payload.background:
        return first_enabled(["queue", "json_rpc", "rest"], service)
    if payload.realtime and payload.bidirectional:
        return first_enabled(["websocket", "sse"], service)
    if payload.realtime:
        return first_enabled(["sse", "websocket"], service)
    return first_enabled([service.default_api_interface, action["interface"], "rest"], service)


def first_enabled(candidates: list[str], service: ServiceSettings) -> str:
    for candidate in candidates:
        if candidate in service.enabled_interfaces:
            return candidate
    return service.enabled_interfaces[0]


def endpoint_for_interface(interface: str, action: dict[str, Any]) -> str:
    if interface == "python_sdk":
        return "tg_api_zapret.TgApiZapretClient"
    if interface == "queue":
        return action.get("queue", "POST /queue/jobs")
    if interface == "websocket":
        return action.get("websocket", "WS /ws/updates")
    if interface == "sse":
        return action.get("sse", "GET /events")
    if interface == "json_rpc":
        return "POST /rpc"
    return action.get("rest", "POST /raw/invoke")


def reason_for_interface(interface: str, payload: ActionResolvePayload) -> str:
    if interface == "python_sdk":
        return "Python client requested; SDK hides HTTP details."
    if interface == "queue":
        return "Background execution requested."
    if interface == "websocket":
        return "Realtime bidirectional stream requested."
    if interface == "sse":
        return "Realtime one-way event stream requested."
    if interface == "json_rpc":
        return "Command can be routed through the generic RPC endpoint."
    return "Simple request/response command."


def resolve_session_file(session_file: Path, account: str) -> Path:
    if account == "default":
        return session_file
    return session_file.parent / "sessions" / f"{account}.session.txt"


def serialize_user(user: User | None) -> dict[str, Any]:
    if user is None:
        return {}
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "bot": user.bot,
    }


def serialize_dialog(dialog: Dialog) -> dict[str, Any]:
    entity = getattr(dialog, "entity", None)
    input_entity = None
    if entity is not None:
        try:
            input_entity = utils.get_input_peer(entity)
        except TypeError:
            input_entity = None
    return {
        "id": dialog.id,
        "name": dialog.name,
        "title": dialog.title,
        "username": getattr(entity, "username", None),
        "entity_type": type(entity).__name__ if entity is not None else None,
        "access_hash": getattr(entity, "access_hash", None),
        "input_entity": serialize_tl(input_entity) if input_entity is not None else None,
        "is_user": dialog.is_user,
        "is_group": dialog.is_group,
        "is_channel": dialog.is_channel,
        "unread_count": dialog.unread_count,
    }


def serialize_message(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "date": message.date.isoformat() if message.date else None,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "text": message.message,
        "out": message.out,
        "mentioned": message.mentioned,
        "media": type(message.media).__name__ if message.media else None,
    }
