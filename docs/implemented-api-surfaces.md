# tg-api-zapret 0.4.21 implemented API surfaces

## Compatibility levels

- Level A: Bot API compatibility endpoint is implemented at `/bot{token}/{method}`.
  Supported methods: `getMe`, `getUpdates`, `sendMessage`, `sendPhoto`, `sendDocument`,
  `editMessageText`, `deleteMessage`. This is a compatibility layer, not a full Telegram
  Bot API proxy.
- Level B: Reverse-proxy/DNS compatibility information is exposed at `/compat/reverse-proxy`.
  This is for applications that already use Telegram Bot API HTTPS and can change base URL,
  DNS, or reverse-proxy routing.
- Level C: Python drop-in SDK adapters are implemented in `tg_api_zapret.sdk`.
  Use `TgApiZapretClient` for native API calls and `BotApiAdapter` for Bot API style calls.

## Requested items 1-8

1. TL JSON decoder/encoder: implemented in `tg_api_zapret/tl_codec.py`.
   It supports constructors like `{"_":"InputPeerUser","user_id":1,"access_hash":2}`,
   nested lists/objects, `{"_":"bytes","base64":"..."}`, `{"_":"datetime","iso":"..."}`,
   and Telethon optional/flag fields through constructor kwargs.
2. Entity resolver: implemented in `tg_api_zapret/tl_codec.py`.
   Raw/layer requests can pass fields such as `{"peer":"@username"}` and the API resolves
   them with Telethon `get_input_entity`/`get_entity` based on TL annotations.
3. Convenient wrappers: implemented as REST and JSON-RPC surfaces for message send/edit/delete,
   media send/download/upload, entity resolve, join/leave channels, delete history, reactions,
   stories get/send, and admin ban/promote.
4. Type constructor API: implemented at `POST /tl/construct`.
5. Stable response serialization: implemented through `serialize_tl`.
   Bytes, dates, TL objects, lists, dicts and primitive values are JSON-safe.
6. CORS middleware: implemented from `service.cors_origins`.
7. Request timeout middleware: implemented from `service.request_timeout_seconds`.
8. Production queue workers: Redis queues are no longer executed inside the API process.
   Redis jobs include idempotency keys, attempts/max attempts, leases, retry, and dead-letter
   state for exhausted jobs.

## Telegram Desktop-like presence

- Default client profile uses `device_model=Telegram Desktop` and `system_version=Linux x86_64`.
- Authorized accounts can be kept connected with `POST /accounts/connect`.
- Stored authorized accounts can be connected on API startup with `auto_connect_accounts`.
- Connected authorized accounts can run a reconnect loop with bounded backoff.
- A passive MTProto update receiver keeps the client subscribed to raw updates.
- Entity cache warmup stores recent dialog usernames and input-entity data for faster reuse.
- `GET /accounts/health` checks Telegram/proxy connectivity before sensitive auth flows.
- Presence heartbeat uses MTProto `account.UpdateStatus(offline=False)` every
  `online_update_interval_seconds` seconds while the API process is running.
- `GET /accounts/online` reports heartbeat, reconnect, passive receiver, and health status.
- `POST /accounts/entity-cache/warm` and `GET /accounts/entity-cache` manage the runtime cache.
- `POST /accounts/disconnect` stops the heartbeat and disconnects the account.

## Redis queue mode

Run API:

```bash
python -m tg_api_zapret api --host 0.0.0.0 --port 8081 --queue-backend redis --redis-url redis://127.0.0.1:6379/0
```

Run one or more workers:

```bash
python -m tg_api_zapret worker --redis-url redis://127.0.0.1:6379/0
```

## Bot token to account mapping

Configure with `PATCH /app/settings`:

```json
{
  "bot_token_accounts": {
    "123456:token": "work"
  }
}
```

If a token is not mapped, the active account is used.

## Drop-in Bot API examples

```bash
curl -X POST http://127.0.0.1:8081/bot123456:token/sendMessage \
  -H 'Content-Type: application/json' \
  -d '{"chat_id":"@username","text":"hello"}'
```

```python
from tg_api_zapret import BotApiAdapter

bot = BotApiAdapter("http://127.0.0.1:8081", "123456:token")
bot.send_message("@username", "hello")
```

## Raw MTProto examples

```json
{
  "request": "messages.SendMessageRequest",
  "kwargs": {
    "peer": "@username",
    "message": "hello",
    "random_id": 123456789
  }
}
```

```json
{
  "constructor": "InputPeerUser",
  "fields": {
    "user_id": 123,
    "access_hash": 456
  }
}
```
