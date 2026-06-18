# tg-api-zapret

Асинхронная прослойка для подключения к Telegram через MTProto. Низкоуровневую часть
протокола выполняет Telethon, а этот пакет дает единый слой для конфигурации,
авторизации, хранения сессий и типовых операций.

## Возможности

- конфигурация официального desktop-клиента Telegram по умолчанию;
- хранение `StringSession` в файле, переменной окружения, строке или SQLite;
- первичная авторизация по телефону, коду и 2FA-паролю;
- повторное подключение без повторной авторизации;
- высокоуровневые методы `send_message`, `get_dialogs`, `iter_messages`, `stream_updates`;
- raw RPC через `invoke`;
- SOCKS4, SOCKS5 и HTTP proxy через `TELEGRAM_PROXY_URL`.

## Установка на Ubuntu

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Если проект запускается прямо из папки без установки пакета, поставьте runtime-зависимости:

```bash
python -m pip install -r requirements.txt
```

Для прокси Telethon 1.44 требует пакет `python-socks`:

```bash
python -m pip install "python-socks[asyncio]>=2.4,<3.0"
```

## Переменные окружения

```bash
export TELEGRAM_API_ID=2040
export TELEGRAM_API_HASH=b18441a1ff607e10a989891a5462e627
# опционально:
export TELEGRAM_PROXY_URL=socks5://user:password@127.0.0.1:1080
```

Если переменные `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` не заданы, используются
значения desktop-клиента из технического задания.

## Первичная авторизация

```bash
python -m tg_api_zapret --session-file ~/.config/tg-api-zapret/session.txt login
```

Программа последовательно спросит номер телефона, код подтверждения и, если на
аккаунте включена двухэтапная проверка, 2FA-пароль. После успешного входа session
string будет сохранена в файл с правами `0600`.
На следующих запусках код подтверждения больше не нужен.

Номер также можно передать сразу:

```bash
python -m tg_api_zapret --session-file ~/.config/tg-api-zapret/session.txt login +79990000000
```

Сессия сохраняется и не должна теряться при перезапуске, если запускать программу
от того же Linux-пользователя и с тем же `--session-file`. По умолчанию это:

```text
~/.config/tg-api-zapret/session.txt
```

## Несколько аккаунтов

Аккаунты именуются произвольно. Активный аккаунт хранится в config-файле.

Создать или переключить активный аккаунт:

```bash
python -m tg_api_zapret use-account work
```

Залогиниться в выбранный аккаунт:

```bash
python -m tg_api_zapret --account work login
```

Посмотреть аккаунты:

```bash
python -m tg_api_zapret accounts
```

В файловом режиме сессии хранятся так:

- `default` - `~/.config/tg-api-zapret/session.txt`
- остальные - `~/.config/tg-api-zapret/sessions/<account>.session.txt`

Пример обращения к разным аккаунтам:

```bash
python -m tg_api_zapret --account work dialogs
python -m tg_api_zapret --account personal send me "hello"
```

Проверка:

```bash
python -m tg_api_zapret --session-file ~/.config/tg-api-zapret/session.txt status
```

Отправка сообщения:

```bash
python -m tg_api_zapret --session-file ~/.config/tg-api-zapret/session.txt send me "test message"
```

## Использование как библиотеки

```python
import asyncio

from tg_api_zapret import FileSessionBackend, TelegramConfig, TelegramLayer


async def main() -> None:
    layer = TelegramLayer(
        TelegramConfig.from_env(),
        FileSessionBackend("telegram.session.txt"),
    )
    async with layer.lifespan():
        await layer.send_message("me", "Hello")


asyncio.run(main())
```

## SQLite-хранилище сессии

```bash
python -m tg_api_zapret --session-db ~/.config/tg-api-zapret/sessions.sqlite3 --session-key main login
```

## Интерактивное меню

```bash
python -m tg_api_zapret --menu
```

В меню можно запустить прослойку и авторизацию, проверить статус, отправить
сообщение, вывести диалоги, указать прокси, поменять имя клиента или запустить
HTTP API.

## Имя в авторизованных приложениях Telegram

По умолчанию прослойка авторизуется с `device_model=tg-api-zapret` и
`app_version`, равным текущей версии `tg-api-zapret`. Это имя Telegram обычно
показывает в списке активных устройств.

Изменить профиль клиента:

```bash
python -m tg_api_zapret set-client-profile \
  --device-model tg-api-zapret \
  --system-version Ubuntu \
  --app-version 0.2.6
```

Для уже существующей сессии Telegram может оставить старое название. Надежный
способ увидеть новое имя в активных устройствах - задать профиль до первого
логина или перелогиниться.

Версия приложения ведется в `tg_api_zapret/version.py` и дублируется в
`pyproject.toml`. При каждом обновлении проекта номер версии нужно повышать.

## Прокси для Telegram

Прокси можно сохранить в конфиге приложения:

```bash
python -m tg_api_zapret set-proxy socks5d://127.0.0.1:1080
```

Поддерживаемые схемы:

- `http://host:port`
- `https://host:port`
- `socks5://host:port`
- `socks5d://host:port`
- `socks5h://host:port`
- `socks5://user:password@host:port`
- `socks5d://user:password@host:port`
- `socks5h://user:password@host:port`

`socks5d` и `socks5h` включают разрешение доменов через прокси. `socks5`
оставляет DNS на стороне машины, где запущена программа.

Посмотреть текущую настройку:

```bash
python -m tg_api_zapret show-config
```

Удалить прокси:

```bash
python -m tg_api_zapret clear-proxy
```

Переменная окружения `TELEGRAM_PROXY_URL` тоже поддерживается, но сохраненный
прокси из config-файла имеет приоритет.

## HTTP API

Запуск API:

```bash
python -m tg_api_zapret api --host 127.0.0.1 --port 8080
```

OpenAPI-документация будет доступна по адресу:

```text
http://127.0.0.1:8080/docs
```

Первые эндпоинты:

- `GET /accounts`
- `POST /accounts`
- `GET /health`
- `GET /config`
- `PUT /config/proxy`
- `PUT /config/client-profile`
- `GET /auth/status`
- `POST /auth/send-code`
- `POST /auth/confirm-code`
- `POST /auth/password`
- `GET /me`
- `GET /dialogs`
- `GET /messages/{entity}`
- `POST /messages/send`
- `POST /messages/edit`
- `POST /messages/delete`
- `POST /messages/forward`
- `POST /raw/invoke`
- `POST /rpc`
- `GET /events`
- `WS /ws/updates`
- `POST /queue/jobs`
- `GET /queue/jobs`
- `GET /queue/jobs/{job_id}`
- `GET /capabilities`
- `POST /actions/resolve`
- `POST /actions/execute`

Пример отправки сообщения:

```bash
curl -X POST http://127.0.0.1:8080/messages/send \
  -H 'Content-Type: application/json' \
  -d '{"entity":"me","text":"hello from API"}'
```

Выбор аккаунта в API делается query-параметром `account`:

```bash
curl 'http://127.0.0.1:8080/dialogs?account=work&limit=20'
curl -X POST 'http://127.0.0.1:8080/messages/send?account=personal' \
  -H 'Content-Type: application/json' \
  -d '{"entity":"me","text":"hello from personal"}'
```

`/raw/invoke` нужен как аварийный выход к TL-функциям Telethon, пока для нужной
операции еще нет отдельного удобного эндпоинта.

Полный список MTProto definitions из установленной TL-схемы Telethon:

- `docs/mtproto-definitions.md`
- `docs/mtproto-definitions.json`
- `docs/mtproto-importance-layers.md`
- `docs/mtproto-importance-layers.json`

В Telethon `1.44.0` сейчас получается `2344` definitions:

- `779` request-функций
- `1565` TL type constructors

Отдельный список только MTProto request-функций:

- `docs/mtproto-functions.md`
- `docs/mtproto-functions.json`

Пересоздать справочники:

```bash
python scripts/generate_mtproto_docs.py
python scripts/generate_mtproto_importance_layers.py
```

## Automatic API Method Selection

Клиентское приложение может не выбирать REST/WebSocket/SSE/Queue вручную. Для
этого есть resolver:

```bash
curl -X POST http://127.0.0.1:8080/actions/resolve \
  -H 'Content-Type: application/json' \
  -d '{"task":"send message","account":"work","params":{"entity":"me","text":"hello"}}'
```

Ответ содержит рекомендуемый интерфейс, endpoint и причину выбора:

```json
{
  "action": "send_message",
  "interface": "rest",
  "endpoint": "POST /messages/send",
  "rpc_method": "messages.send",
  "reason": "Simple request/response command."
}
```

Если задачу нужно выполнить в фоне:

```bash
curl -X POST http://127.0.0.1:8080/actions/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"send message","account":"work","background":true,"params":{"entity":"me","text":"queued"}}'
```

Для realtime-задач resolver выберет SSE или WebSocket:

```bash
curl -X POST http://127.0.0.1:8080/actions/resolve \
  -H 'Content-Type: application/json' \
  -d '{"task":"new messages","account":"work","realtime":true}'
```

Python SDK тоже умеет выбирать метод:

```python
from tg_api_zapret import TgApiZapretClient

client = TgApiZapretClient()
plan = client.resolve_action(
    "send message",
    account="work",
    params={"entity": "me", "text": "hello"},
)
print(plan)

result = client.execute_action(
    "send message",
    account="work",
    params={"entity": "me", "text": "hello"},
)
print(result)
```

Список возможностей:

```bash
curl http://127.0.0.1:8080/capabilities
```

## WebSocket API

Поток новых сообщений:

```text
ws://127.0.0.1:8080/ws/updates?account=work
```

Каждое событие приходит JSON-сообщением.

## SSE API

Односторонний поток событий через Server-Sent Events:

```bash
curl -N 'http://127.0.0.1:8080/events?account=work'
```

## JSON-RPC API

Один endpoint для команд:

```bash
curl -X POST http://127.0.0.1:8080/rpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"messages.send","params":{"account":"work","entity":"me","text":"hello"}}'
```

Поддерживаемые методы:

- `accounts.list`
- `auth.status`
- `dialogs.list`
- `messages.send`
- `raw.invoke`

## Queue API

In-memory очередь фоновых задач:

```bash
curl -X POST http://127.0.0.1:8080/queue/jobs \
  -H 'Content-Type: application/json' \
  -d '{"kind":"messages.send","account":"work","payload":{"entity":"me","text":"queued hello"}}'
```

Проверить задачу:

```bash
curl http://127.0.0.1:8080/queue/jobs/<job_id>
```

Сейчас очередь хранится в памяти процесса. Для production-нагрузки следующим
слоем можно подключить Redis, RabbitMQ или NATS без изменения внешнего API.

Запуск API с Redis backend:

```bash
python -m tg_api_zapret api \
  --host 127.0.0.1 \
  --port 8080 \
  --queue-backend redis \
  --redis-url redis://127.0.0.1:6379/0
```

Через переменные окружения:

```bash
export TG_API_QUEUE_BACKEND=redis
export REDIS_URL=redis://127.0.0.1:6379/0
python -m tg_api_zapret api --host 127.0.0.1 --port 8080
```

Redis выбран как первый production backend: для текущего Queue API важнее хранить
статусы задач и быстро поднимать сервис без сложной инфраструктуры. RabbitMQ/NATS
можно добавить позже тем же backend-интерфейсом, если понадобится отдельный
кластер воркеров или pub/sub-шина.

## Python SDK API

```python
from tg_api_zapret import TgApiZapretClient

client = TgApiZapretClient("http://127.0.0.1:8080")
print(client.health())
print(client.dialogs(account="work", limit=20))
client.send_message("me", "hello from sdk", account="work")

job = client.enqueue(
    "messages.send",
    {"entity": "me", "text": "queued from sdk"},
    account="work",
)
print(client.job(job["id"]))
```

## Raw RPC

```python
from telethon.tl.functions.users import GetFullUserRequest

result = await layer.invoke(GetFullUserRequest("me"))
```

## Запуск тестов

```bash
pytest
```
