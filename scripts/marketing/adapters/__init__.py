"""Thin provider adapters for approval-bound marketing execution.

Each adapter exposes ``REQUIRES_ENV``, ``validate(request, approval)``, ``describe(request, approval)`` (the exact
requests that would be sent, without credentials) and ``run(request, approval, *, http, secret)`` returning
``{status, provider_ids}``. Adapters are only reachable through ``scripts/marketing/execute.py``, which enforces the
founder approval; never call ``run`` directly.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request


class AdapterError(RuntimeError):
    """A provider refused or failed the request; the message never contains credentials.

    ``uncertain`` marks failures after a provider may already have acted; ``provider_ids`` keeps ids created so far.
    """

    def __init__(self, message: str, *, provider_ids: dict | None = None, uncertain: bool = False):
        super().__init__(message)
        self.provider_ids = provider_ids or {}
        self.uncertain = uncertain


def require_secret(secret, name: str) -> str:
    _, value = secret(name)
    if not value:
        raise AdapterError(f"missing environment variable {name}")
    return value


def urllib_http(method: str, url: str, headers: dict, body: dict | None):
    """Default JSON transport. Tests inject a fake; this task never performs a live call."""
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json", "Accept": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed provider hosts or env base URL
            raw = response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        raise AdapterError(f"{method} {url} failed with HTTP {exc.code}") from None
    return json.loads(raw or b"{}")


def first_id(response, *keys: str):
    if isinstance(response, list):
        return [first_id(item, *keys) for item in response]
    if isinstance(response, dict):
        for key in keys:
            if response.get(key) is not None:
                return response[key]
    return None
