from tg_api_zapret.sessions import (
    FileSessionBackend,
    SQLiteSessionBackend,
    StaticStringSessionBackend,
    TelethonSessionFileBackend,
    decode_session_from_transport,
    encode_session_for_transport,
)


def test_static_session_backend_roundtrip() -> None:
    backend = StaticStringSessionBackend()
    assert backend.load() is None

    backend.save("abc")

    assert backend.load() == "abc"


def test_file_session_backend_roundtrip(tmp_path) -> None:
    backend = FileSessionBackend(tmp_path / "session.txt")

    backend.save("session-value")

    assert backend.load() == "session-value"


def test_sqlite_session_backend_roundtrip(tmp_path) -> None:
    backend = SQLiteSessionBackend(tmp_path / "sessions.sqlite3", key="main")

    backend.save("session-value")

    assert backend.load() == "session-value"


def test_telethon_session_file_backend_uses_native_path(tmp_path) -> None:
    path = tmp_path / "native.session"
    backend = TelethonSessionFileBackend(path)

    assert backend.client_session() == str(path)
    assert backend.load() is None


def test_transport_encoding_roundtrip() -> None:
    encoded = encode_session_for_transport("session-value")

    assert decode_session_from_transport(encoded) == "session-value"
