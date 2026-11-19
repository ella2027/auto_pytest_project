"""Reusable HTTP client for API tests."""
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from common.logger import logger
from configs.settings import BASE_URL, DEFAULT_HEADERS


class ApiClient:
    """Small requests.Session wrapper with shared base URL and headers."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = (base_url if base_url is not None else BASE_URL).strip().rstrip("/")
        if not self.base_url:
            raise RuntimeError(
                "Missing API base URL. Copy .env.example to .env and set "
                "<ENV>_BASE_URL (for example TEST_BASE_URL)."
            )
        self.headers = dict(DEFAULT_HEADERS if headers is None else headers)
        self.session = session or requests.Session()

    def _build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _merge_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        return {**self.headers, **(headers or {})}

    @staticmethod
    def _log_and_return(response: requests.Response) -> requests.Response:
        logger.debug(
            "[%s] %s -> %s (%.3fs)",
            response.request.method,
            response.request.url,
            response.status_code,
            response.elapsed.total_seconds(),
        )
        return response

    def get(self, path: str, params: Optional[dict] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
        response = self.session.get(self._build_url(path), params=params,
                                    headers=self._merge_headers(headers), **kwargs)
        return self._log_and_return(response)

    def post(self, path: str, json: Optional[dict] = None,
             headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
        response = self.session.post(self._build_url(path), json=json,
                                     headers=self._merge_headers(headers), **kwargs)
        return self._log_and_return(response)

    def put(self, path: str, json: Optional[dict] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
        response = self.session.put(self._build_url(path), json=json,
                                    headers=self._merge_headers(headers), **kwargs)
        return self._log_and_return(response)

    def delete(self, path: str, headers: Optional[Dict[str, str]] = None,
               **kwargs: Any) -> requests.Response:
        response = self.session.delete(self._build_url(path),
                                       headers=self._merge_headers(headers), **kwargs)
        return self._log_and_return(response)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
