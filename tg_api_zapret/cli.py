from __future__ import annotations

import argparse
import asyncio
from getpass import getpass
import os
from pathlib import Path
import sys
from typing import Sequence

from telethon.errors import SessionPasswordNeededError

from tg_api_zapret.client import TelegramLayer
from tg_api_zapret.config import TelegramConfig
from tg_api_zapret.sessions import FileSessionBackend, SQLiteSessionBackend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tg-api-zapret")
    parser.add_argument(
        "--session-file",
        default="~/.config/tg-api-zapret/session.txt",
        help="Path for StringSession storage.",
    )
    parser.add_argument("--session-db", help="SQLite database for session storage.")
    parser.add_argument("--session-key", default="default", help="SQLite session key.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Authorize and persist a Telegram session.")
    login.add_argument("phone", help="Phone number in international format.")
    login.add_argument(
        "--password-env",
        default="TELEGRAM_2FA_PASSWORD",
        help="Environment variable with Telegram two-step password.",
    )

    request_code = subparsers.add_parser("request-code", help="Send a Telegram login code.")
    request_code.add_argument("phone", help="Phone number in international format.")

    confirm_code = subparsers.add_parser("confirm-code", help="Confirm a Telegram login code.")
    confirm_code.add_argument("phone", help="Phone number in international format.")
    confirm_code.add_argument("phone_code_hash", help="Hash returned by request-code.")
    confirm_code.add_argument("code", help="Telegram login code.")
    confirm_code.add_argument(
        "--password-env",
        default="TELEGRAM_2FA_PASSWORD",
        help="Environment variable with Telegram two-step password.",
    )

    subparsers.add_parser("status", help="Print authorization status.")

    send = subparsers.add_parser("send", help="Send a text message.")
    send.add_argument("entity", help="Username, phone, chat id, or peer.")
    send.add_argument("text", help="Message text.")

    dialogs = subparsers.add_parser("dialogs", help="List dialogs.")
    dialogs.add_argument("--limit", type=int, default=20)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    asyncio.run(run(args))


async def run(args: argparse.Namespace) -> None:
    if args.session_db:
        backend = SQLiteSessionBackend(Path(args.session_db), args.session_key)
    else:
        backend = FileSessionBackend(Path(args.session_file))

    layer = TelegramLayer(TelegramConfig.from_env(), backend)

    async with layer.lifespan():
        if args.command == "login":
            sent_code = await layer.send_code(args.phone)
            try:
                await layer.sign_in(sent_code, input("Telegram code: ").strip())
            except SessionPasswordNeededError:
                await layer.sign_in_password(read_password(args.password_env))
            print("authorized")
        elif args.command == "request-code":
            sent_code = await layer.send_code(args.phone)
            print(sent_code.phone_code_hash)
        elif args.command == "confirm-code":
            from tg_api_zapret.client import SentCode

            sent_code = SentCode(phone=args.phone, phone_code_hash=args.phone_code_hash)
            try:
                await layer.sign_in(sent_code, args.code)
            except SessionPasswordNeededError:
                await layer.sign_in_password(read_password(args.password_env))
            print("authorized")
        elif args.command == "status":
            print("authorized" if await layer.is_authorized() else "not authorized")
        elif args.command == "send":
            await layer.send_message(args.entity, args.text)
            print("sent")
        elif args.command == "dialogs":
            dialogs = await layer.get_dialogs(limit=args.limit)
            for dialog in dialogs:
                print(f"{dialog.id}\t{dialog.name}")
        else:
            raise ValueError(f"Unsupported command: {args.command}")


def read_password(env_name: str) -> str:
    value = os.getenv(env_name)
    if value:
        return value
    if sys.stdin.isatty():
        return getpass("Two-step password: ")
    raise RuntimeError(
        f"Telegram two-step password is required. Set {env_name} or run from an interactive TTY."
    )


if __name__ == "__main__":
    main()
