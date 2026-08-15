"""HTTP client for the public ODIS Search API (odis-ui FastAPI facade)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

DEFAULT_BASE_URL = "https://search-demo.odis.org"
DEFAULT_BACKEND = "elasticsearch"
DEFAULT_TIMEOUT = 30
MAX_PAGE_SIZE = 50


class OdisSearchError(RuntimeError):
    """Raised when the ODIS Search API returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class OdisSearchClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        backend: str = DEFAULT_BACKEND,
        timeout: float = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.backend = backend
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "x-search-backend": self.backend,
        }

    def search(
        self,
        q: str | None = None,
        *,
        types: list[str] | None = None,
        sources: list[str] | None = None,
        sort: str = "relevance",
        page: int = 1,
        size: int = 20,
        include_graph_fragments: bool = False,
    ) -> dict[str, Any]:
        if size < 1 or size > MAX_PAGE_SIZE:
            raise ValueError(f"size must be between 1 and {MAX_PAGE_SIZE}")
        if page < 1:
            raise ValueError("page must be >= 1")

        params: list[tuple[str, str]] = [
            ("sort", sort),
            ("page", str(page)),
            ("size", str(size)),
            ("include_graph_fragments", "true" if include_graph_fragments else "false"),
        ]
        if q:
            params.append(("q", q))
        for value in types or []:
            if value:
                params.append(("types", value))
        for value in sources or []:
            if value:
                params.append(("source", value))

        response = self.session.get(
            f"{self.base_url}/api/v1/search",
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._json(response)

    def get_record(self, record_id: str, *, raw: bool = True) -> dict[str, Any] | None:
        encoded = quote(record_id, safe="")
        response = self.session.get(
            f"{self.base_url}/api/v1/records/{encoded}",
            params={"raw": "true" if raw else "false"},
            headers=self._headers(),
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return None
        return self._json(response)

    def health(self) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/v1/health",
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._json(response)

    @staticmethod
    def _json(response: requests.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise OdisSearchError(
                f"Request failed: {exc}",
                status_code=response.status_code,
                body=response.text,
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise OdisSearchError(
                "Response was not JSON",
                status_code=response.status_code,
                body=response.text,
            ) from exc
        if not isinstance(payload, dict):
            raise OdisSearchError("Unexpected JSON payload", status_code=response.status_code)
        return payload
