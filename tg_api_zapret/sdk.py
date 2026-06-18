from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TgApiZapretClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8080") -> None:
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def accounts(self) -> dict[str, Any]:
        return self._request("GET", "/accounts")

    def auth_status(self, account: str | None = None) -> dict[str, Any]:
        return self._request("GET", "/auth/status", query=account_query(account))

    def dialogs(self, account: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return self._request("GET", "/dialogs", query={**account_query(account), "limit": limit})

    def send_message(
        self,
        entity: str | int,
        text: str,
        *,
        account: str | None = None,
        parse_mode: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/messages/send",
            query=account_query(account),
            body={"entity": entity, "text": text, "parse_mode": parse_mode},
        )

    def rpc(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/rpc",
            body={"jsonrpc": "2.0", "method": method, "params": params or {}, "id": request_id},
        )

    def enqueue(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        account: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/queue/jobs",
            body={"kind": kind, "account": account, "payload": payload},
        )

    def job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/queue/jobs/{job_id}")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/capabilities")

    def app_settings(self) -> dict[str, Any]:
        return self._request("GET", "/app/settings")

    def update_app_settings(self, **settings: Any) -> dict[str, Any]:
        return self._request("PATCH", "/app/settings", body=settings)

    def resolve_action(
        self,
        task: str,
        *,
        account: str | None = None,
        params: dict[str, Any] | None = None,
        realtime: bool = False,
        background: bool = False,
        bidirectional: bool = False,
        client_language: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/actions/resolve",
            body={
                "task": task,
                "account": account,
                "params": params or {},
                "realtime": realtime,
                "background": background,
                "bidirectional": bidirectional,
                "client_language": client_language,
            },
        )

    def execute_action(
        self,
        task: str,
        *,
        account: str | None = None,
        params: dict[str, Any] | None = None,
        realtime: bool = False,
        background: bool = False,
        bidirectional: bool = False,
        client_language: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/actions/execute",
            body={
                "task": task,
                "account": account,
                "params": params or {},
                "realtime": realtime,
                "background": background,
                "bidirectional": bidirectional,
                "client_language": client_language,
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = self.base_url + path
        if query:
            clean_query = {key: value for key, value in query.items() if value is not None}
            if clean_query:
                url += "?" + urlencode(clean_query)

        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method)
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))


def account_query(account: str | None) -> dict[str, str]:
    return {"account": account} if account else {}
