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
сообщение, вывести диалоги, указать прокси или очистить настройки прокси.

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

## Raw RPC

```python
from telethon.tl.functions.users import GetFullUserRequest

result = await layer.invoke(GetFullUserRequest("me"))
```

## Запуск тестов

```bash
pytest
```
