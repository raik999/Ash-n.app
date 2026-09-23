from __future__ import annotations

import os
from typing import Any

import httpx

API_BASE_URL = os.getenv("ASHUN_API_URL", "http://localhost:8000")

REQUEST_TIMEOUT = 20.0


class ApiError(Exception):
    def __init__(self, message: str, *, field: str | None = None, status: int = 0):
        super().__init__(message)
        self.message = message
        self.field = field
        self.status = status


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._token: str | None = None

    def set_token(self, token: str | None) -> None:
        self._token = token

    @property
    def token(self) -> str | None:
        return self._token

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.request(
                    method,
                    url,
                    json=json,
                    files=files,
                    headers=self._headers(),
                )
        except httpx.ConnectError:
            raise ApiError(
                "No se pudo conectar con el servidor.\n"
                f"Revisa que el backend este corriendo en {self.base_url}",
                status=0,
            ) from None
        except httpx.TimeoutException:
            raise ApiError("El servidor tardo demasiado en responder", status=0) from None

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code == 204:
            return None

        try:
            data = response.json()
        except ValueError:
            data = None

        if response.is_success:
            return data

        message = "Ocurrio un error inesperado"
        field = None

        if isinstance(data, dict):
            detail = data.get("detail")
            if isinstance(detail, str):
                message = detail
            field = data.get("field")

        raise ApiError(message, field=field, status=response.status_code)

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self.request("PATCH", path, json=json)

    def delete(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, json=json)

    def upload(self, path: str, field_name: str, filename: str, content: bytes, mime: str) -> Any:
        return self.request(
            "POST",
            path,
            files={field_name: (filename, content, mime)},
        )

    def absolute_url(self, path: str | None) -> str | None:
        if not path:
            return None
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}{path}"


api = ApiClient()
