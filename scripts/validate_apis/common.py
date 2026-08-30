#!/usr/bin/env python3
"""Shared helpers for Evidence Scout API validation scripts."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


USER_AGENT = "evidence-scout-validator/0.1"


def project_root() -> Path:
    current = Path.cwd().resolve()
    for path in [current, *current.parents]:
        if (path / "AGENTS.md").exists():
            return path
    return current


ROOT = project_root()
OUTPUT_DIR = ROOT / "research" / "evidence-scout" / "api-validation"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_local_secrets() -> dict[str, str]:
    """Load simple KEY=VALUE lines from ~/.secrets without overriding env vars."""
    secrets_path = Path.home() / ".secrets"
    loaded: dict[str, str] = {}
    if not secrets_path.exists() or not secrets_path.is_file():
        return loaded
    try:
        for raw_line in secrets_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and value and key not in os.environ:
                loaded[key] = value
                os.environ[key] = value
    except PermissionError:
        loaded["_error"] = f"Permission denied reading {secrets_path}"
    except OSError as exc:
        loaded["_error"] = f"Could not read {secrets_path}: {exc}"
    return loaded


def get_secret(*names: str) -> tuple[str | None, str | None]:
    load_local_secrets()
    resolved_names: list[str] = []
    for name in names:
        if name == "FIRECRAWL_API_KEY":
            resolved_names.append("FIRECRAWL_API_KEY_HGINVESTOR")
        else:
            resolved_names.append(name)
    for name in resolved_names:
        value = os.environ.get(name)
        if value:
            return name, value
    return None, None


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            lower = key.lower()
            if lower in {"access_token", "refresh_token", "id_token", "client_secret", "api_key", "token", "secret"}:
                redacted[key] = "***"
            elif "authorization" in lower or "cookie" in lower:
                redacted[key] = "***"
            elif "token" in lower or "secret" in lower or lower.endswith("_key"):
                redacted[key] = "***"
            else:
                redacted[key] = redact_sensitive(child)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(child) for child in value]
    if isinstance(value, str):
        value = re.sub(
            r"(?i)([?&](?:access_token|refresh_token|id_token|token|signature|x-signature|api_key|key|client_secret)=)[^&\s\"']+",
            r"\1***",
            value,
        )
        value = re.sub(
            r"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s\"']+",
            r"\1***",
            value,
        )
        return value
    return value


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, value in headers.items():
        lower = key.lower()
        if lower in {"authorization", "cookie", "set-cookie", "x-api-key"}:
            safe[key] = "***"
        elif "token" in lower or "secret" in lower or "key" in lower:
            safe[key] = "***"
        else:
            safe[key] = value
    return safe


def http_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: Any | None = None,
    basic_auth: tuple[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    body: bytes | None = None
    if data is not None:
        if isinstance(data, bytes):
            body = data
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = json.dumps(data).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
    if basic_auth:
        token = base64.b64encode(f"{basic_auth[0]}:{basic_auth[1]}".encode("utf-8")).decode("ascii")
        request_headers["Authorization"] = f"Basic {token}"

    req = urllib.request.Request(url, data=body, headers=request_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw_body = response.read()
            text = raw_body.decode("utf-8", errors="replace")
            parsed: Any
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = {"text": text[:20000]}
            return {
                "ok": True,
                "status_code": response.status,
                "headers": sanitize_headers(dict(response.headers.items())),
                "body": parsed,
            }
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"text": text[:20000]}
        return {
            "ok": False,
            "status_code": exc.code,
            "headers": sanitize_headers(dict(exc.headers.items())),
            "body": parsed,
            "error": str(exc),
        }
    except Exception as exc:  # Network and TLS failures need to be captured as validation output.
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "body": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def http_get(url: str, **kwargs: Any) -> dict[str, Any]:
    return http_request("GET", url, **kwargs)


def http_post(url: str, **kwargs: Any) -> dict[str, Any]:
    return http_request("POST", url, **kwargs)


def with_query(url: str, params: dict[str, Any]) -> str:
    filtered = {key: value for key, value in params.items() if value is not None}
    return f"{url}?{urllib.parse.urlencode(filtered, doseq=True)}"


CREDIT_EXHAUSTION_TOKENS = [
    "insufficient credit",
    "insufficient_credit",
    "not enough credit",
    "out of credit",
    "no credits",
    "credit balance",
    "credits remaining: 0",
    "buy more credits",
    "purchase credits",
    "add credits",
    "top up",
    "top-up",
    "recharge your account",
]


def is_credit_exhaustion(response: dict[str, Any]) -> bool:
    """Detect credit/quota exhaustion signals in a provider response body or error text."""
    haystacks = [str(response.get("error", "")).lower()]
    body = response.get("body")
    if isinstance(body, dict):
        for key in ("message", "error", "error_message", "detail", "status_message"):
            value = body.get(key)
            if isinstance(value, str):
                haystacks.append(value.lower())
        if body.get("success") is False and body.get("message"):
            haystacks.append(str(body.get("message")).lower())
    elif isinstance(body, str):
        haystacks.append(body.lower())
    return any(token in haystack for haystack in haystacks for token in CREDIT_EXHAUSTION_TOKENS)


def status_from_response(response: dict[str, Any]) -> str:
    if response.get("ok"):
        body = response.get("body")
        if isinstance(body, dict) and body.get("success") is False and is_credit_exhaustion(response):
            return "insufficient_credits"
        return "ok"
    code = response.get("status_code")
    error = str(response.get("error", "")).lower()
    body = response.get("body") if isinstance(response.get("body"), dict) else {}
    provider_status = body.get("status_code")
    if is_credit_exhaustion(response):
        return "insufficient_credits"
    if code in {401, 403}:
        if provider_status == 40104:
            return "account_verification_required"
        return "permission_denied"
    if code in {402, 4020}:
        return "billing_required"
    if code == 429:
        return "rate_limited"
    if code == 404:
        return "unsupported"
    if code is None and any(
        token in error
        for token in [
            "name or service not known",
            "temporary failure",
            "timed out",
            "timeout",
            "network is unreachable",
            "connection refused",
            "connection reset",
            "tunnel connection failed",
        ]
    ):
        return "network_blocked_or_sandboxed"
    return "failed"


def finish(provider: str, summary: dict[str, Any], raw: Any) -> int:
    summary = {
        "provider": provider,
        "validated_at": now_iso(),
        **summary,
    }
    write_json(OUTPUT_DIR / f"{provider}.json", redact_sensitive(raw))
    write_json(OUTPUT_DIR / f"{provider}.summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("status") == "ok" else 1


def missing_credentials(provider: str, required: list[str], instructions: list[str]) -> int:
    summary = {
        "status": "missing_credentials",
        "required_env": required,
        "instructions": instructions,
        "secrets_file_supported": str(Path.home() / ".secrets"),
    }
    raw = {"error": "missing credentials", "required_env": required}
    return finish(provider, summary, raw)


def fields_present(data: Any, max_depth: int = 2) -> list[str]:
    found: set[str] = set()

    def walk(value: Any, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else key
                found.add(path)
                walk(child, path, depth + 1)
        elif isinstance(value, list) and value:
            walk(value[0], f"{prefix}[]", depth + 1)

    walk(data, "", 0)
    return sorted(found)[:200]


def cli_arg(name: str, default: str) -> str:
    prefix = f"--{name}="
    for arg in sys.argv[1:]:
        if arg.startswith(prefix):
            return arg[len(prefix) :]
    return default


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
