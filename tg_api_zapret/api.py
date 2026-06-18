from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
import importlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from telethon import events
from telethon.errors import PasswordHashInvalidError, SessionPasswordNeededError
from telethon.tl.custom.dialog import Dialog
from telethon.tl.custom.message import Message
from telethon.tl.types import User

from tg_api_zapret.client import SentCode, TelegramLayer
from tg_api_zapret.config import (
    AppSettings,
    ClientProfile,
    TelegramConfig,
    normalize_account_name,
    validate_proxy_url,
)
from tg_api_zapret.queue_backends import QueueBackend, build_queue_backend
from tg_api_zapret.sessions import FileSessionBackend, SQLiteSessionBackend
from tg_api_zapret.version import __version__


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
        self.queue: QueueBackend = build_queue_backend(queue_backend, redis_url=redis_url)

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
            backend = FileSessionBackend(resolve_session_file(self.session_file, account_name))
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
        return layer

    async def disconnect(self, account: str | None = None) -> None:
        if account is None:
            for layer in self.layers.values():
                await layer.disconnect()
            self.layers.clear()
            await self.queue.close()
            return
        account_name = self.resolve_account(account)
        layer = self.layers.pop(account_name, None)
        if layer:
            await layer.disconnect()

    async def require_layer(self, account: str | None = None) -> TelegramLayer:
        account_name = self.resolve_account(account)
        if account_name not in self.layers:
            return await self.connect(account_name)
        return self.layers[account_name]

    def resolve_account(self, account: str | None = None) -> str:
        return normalize_account_name(account or self.settings().active_account or self.default_account)


class ProxyPayload(BaseModel):
    proxy_url: str | None = None


class AccountPayload(BaseModel):
    account: str


class ClientProfilePayload(BaseModel):
    device_model: str = Field(default="tg-api-zapret", min_length=1)
    system_version: str = Field(default="Linux", min_length=1)
    app_version: str = Field(default=__version__, min_length=1)
    lang_code: str = Field(default="en", min_length=1)
    system_lang_code: str = Field(default="en-US", min_length=1)


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


class RawInvokePayload(BaseModel):
    request: str = Field(
        description="Telethon TL function path, for example users.GetFullUserRequest"
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
            yield
        finally:
            await state.disconnect()

    app = FastAPI(title="tg-api-zapret", version=__version__, lifespan=lifespan)

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
                        "POST /messages/send",
                        "POST /messages/edit",
                        "POST /messages/delete",
                        "POST /messages/forward",
                        "POST /raw/invoke",
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
                    "description": "Background jobs. Backends: memory, redis.",
                    "endpoints": ["POST /queue/jobs", "GET /queue/jobs/{job_id}"],
                },
                "python_sdk": {
                    "description": "Python client wrapper around HTTP/JSON-RPC/Queue APIs.",
                    "class": "tg_api_zapret.TgApiZapretClient",
                },
            },
            "actions": ACTIONS,
        }

    @app.post("/actions/resolve")
    async def resolve_action(payload: ActionResolvePayload) -> dict[str, Any]:
        return resolve_api_method(payload)

    @app.post("/actions/execute")
    async def execute_action(payload: ActionExecutePayload) -> dict[str, Any]:
        plan = resolve_api_method(payload)
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
                "status": "queued",
                "result": None,
                "error": None,
            })
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
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
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
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
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
            "proxy_url": settings.proxy_url,
            "client_profile": settings.client_profile.to_dict(),
            "active_account": settings.active_account,
            "accounts": settings.accounts,
        }

    @app.get("/accounts")
    async def accounts() -> dict[str, Any]:
        settings = state.settings()
        return {"active_account": settings.active_account, "accounts": settings.accounts}

    @app.post("/accounts")
    async def add_account(payload: AccountPayload) -> dict[str, Any]:
        settings = state.settings().with_account(payload.account)
        state.save_settings(settings)
        return {"active_account": settings.active_account, "accounts": settings.accounts}

    @app.put("/config/proxy")
    async def set_proxy(payload: ProxyPayload) -> dict[str, Any]:
        if payload.proxy_url:
            validate_proxy_url(payload.proxy_url)
        settings = state.settings()
        state.save_settings(replace(settings, proxy_url=payload.proxy_url))
        await reconnect(state)
        return {"proxy_url": payload.proxy_url}

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
        layer = await state.require_layer(account)
        sent = await layer.send_code(payload.phone)
        return {
            "account": state.resolve_account(account),
            "phone": sent.phone,
            "phone_code_hash": sent.phone_code_hash,
        }

    @app.post("/auth/confirm-code")
    async def confirm_code(payload: ConfirmCodePayload, account: str | None = None) -> dict[str, str]:
        layer = await state.require_layer(account)
        try:
            await layer.sign_in(
                SentCode(phone=payload.phone, phone_code_hash=payload.phone_code_hash),
                payload.code,
            )
        except SessionPasswordNeededError:
            return {"status": "password_required"}
        return {"status": "authorized"}

    @app.post("/auth/password")
    async def confirm_password(payload: PasswordPayload, account: str | None = None) -> dict[str, str]:
        layer = await state.require_layer(account)
        try:
            await layer.sign_in_password(payload.password)
        except PasswordHashInvalidError as exc:
            raise HTTPException(status_code=400, detail="Invalid two-step password") from exc
        return {"status": "authorized"}

    @app.get("/me")
    async def me(account: str | None = None) -> dict[str, Any]:
        client = await require_authorized_client(state, account)
        return serialize_user(await client.get_me())

    @app.get("/dialogs")
    async def dialogs(limit: int = 20, account: str | None = None) -> list[dict[str, Any]]:
        layer = await state.require_layer(account)
        return [serialize_dialog(dialog) for dialog in await layer.get_dialogs(limit=limit)]

    @app.get("/messages/{entity}")
    async def messages(
        entity: str,
        limit: int = 50,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        layer = await state.require_layer(account)
        return [serialize_message(message) async for message in layer.iter_messages(entity, limit=limit)]

    @app.post("/messages/send")
    async def send_message(
        payload: SendMessagePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        layer = await state.require_layer(account)
        message = await layer.send_message(
            payload.entity,
            payload.text,
            parse_mode=payload.parse_mode,
        )
        return serialize_message(message)

    @app.post("/messages/edit")
    async def edit_message(
        payload: EditMessagePayload,
        account: str | None = None,
    ) -> dict[str, Any]:
        client = await require_authorized_client(state, account)
        message = await client.edit_message(payload.entity, payload.message_id, payload.text)
        return serialize_message(message)

    @app.post("/messages/delete")
    async def delete_messages(
        payload: DeleteMessagesPayload,
        account: str | None = None,
    ) -> dict[str, Any]:
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
        client = await require_authorized_client(state, account)
        result = await client.forward_messages(
            payload.to_entity,
            payload.message_ids,
            from_peer=payload.from_entity,
        )
        messages = result if isinstance(result, list) else [result]
        return [serialize_message(message) for message in messages]

    @app.post("/raw/invoke")
    async def raw_invoke(payload: RawInvokePayload, account: str | None = None) -> dict[str, Any]:
        layer = await state.require_layer(account)
        request_cls = resolve_tl_request(payload.request)
        result = await layer.invoke(request_cls(**payload.kwargs))
        return {"type": type(result).__name__, "result": stringify(result)}

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
        job_id = uuid4().hex
        job = await state.queue.create_job({
            "id": job_id,
            "kind": payload.kind,
            "account": state.resolve_account(payload.account),
            "status": "queued",
            "result": None,
            "error": None,
        })
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

    return app


async def reconnect(state: ApiState) -> None:
    await state.disconnect()


async def require_authorized_client(state: ApiState, account: str | None = None):
    layer = await state.require_layer(account)
    return await layer._require_authorized_client()


async def dispatch_rpc(state: ApiState, method: str, params: dict[str, Any]) -> Any:
    account = params.pop("account", None)
    if method == "accounts.list":
        settings = state.settings()
        return {"active_account": settings.active_account, "accounts": settings.accounts}
    if method == "auth.status":
        layer = await state.require_layer(account)
        return {"account": state.resolve_account(account), "authorized": await layer.is_authorized()}
    if method == "dialogs.list":
        layer = await state.require_layer(account)
        return [
            serialize_dialog(dialog)
            for dialog in await layer.get_dialogs(limit=int(params.get("limit", 20)))
        ]
    if method == "messages.send":
        layer = await state.require_layer(account)
        message = await layer.send_message(
            params["entity"],
            params["text"],
            parse_mode=params.get("parse_mode"),
        )
        return serialize_message(message)
    if method == "raw.invoke":
        layer = await state.require_layer(account)
        request_cls = resolve_tl_request(params["request"])
        result = await layer.invoke(request_cls(**params.get("kwargs", {})))
        return {"type": type(result).__name__, "result": stringify(result)}
    raise ValueError(f"Unknown RPC method: {method}")


async def run_queue_job(state: ApiState, job_id: str, payload: QueueJobPayload) -> None:
    await state.queue.update_job(job_id, status="running")
    try:
        result = await dispatch_rpc(
            state,
            payload.kind,
            {"account": payload.account, **payload.payload},
        )
        await state.queue.update_job(job_id, result=result, status="done")
    except Exception as exc:
        await state.queue.update_job(job_id, error=str(exc), status="failed")


RPC_METHODS = {
    "accounts.list",
    "auth.status",
    "dialogs.list",
    "messages.send",
    "raw.invoke",
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


def resolve_api_method(payload: ActionResolvePayload) -> dict[str, Any]:
    action_name = find_action(payload.task)
    action = ACTIONS[action_name]
    interface = choose_interface(payload, action)
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


def choose_interface(payload: ActionResolvePayload, action: dict[str, Any]) -> str:
    language = (payload.client_language or "").lower()
    if language == "python":
        return "python_sdk"
    if payload.background:
        return "queue"
    if payload.realtime and payload.bidirectional:
        return "websocket"
    if payload.realtime:
        return "sse"
    return action["interface"]


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


def resolve_tl_request(path: str):
    module_name, _, class_name = path.rpartition(".")
    if not module_name or not class_name:
        raise HTTPException(
            status_code=400,
            detail="Use request path like users.GetFullUserRequest",
        )
    module = importlib.import_module(f"telethon.tl.functions.{module_name}")
    return getattr(module, class_name)


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
    return {
        "id": dialog.id,
        "name": dialog.name,
        "title": dialog.title,
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


def stringify(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple):
        return [stringify(item) for item in value]
    if isinstance(value, dict):
        return {str(key): stringify(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return stringify(value.to_dict())
    return str(value)
