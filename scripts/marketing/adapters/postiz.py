"""Postiz public API: schedule a social post (never ``type: now``).

Docs: https://docs.postiz.com/public-api/introduction
POST {POSTIZ_BASE_URL}/public/v1/posts with ``Authorization: <api key>`` (no Bearer prefix). For Postiz cloud the
base URL is https://api.postiz.com; self-hosted instances use their own public API host.
"""
from __future__ import annotations

from . import first_id, require_secret

REQUIRES_ENV = ("POSTIZ_BASE_URL", "POSTIZ_API_KEY")


def validate(request: dict, approval: dict) -> list[str]:
    errors = []
    if request.get("type", "schedule") != "schedule":
        errors.append("postiz adapter only schedules posts (type must be 'schedule')")
    if not str(request.get("date") or "").strip():
        errors.append("postiz post requires a scheduled date")
    posts = request.get("posts")
    if not isinstance(posts, list) or not posts:
        errors.append("postiz post requires at least one channel entry in posts")
    else:
        for item in posts:
            if not isinstance(item, dict) or not (item.get("integration") or {}).get("id") or not item.get("value"):
                errors.append("each postiz post needs integration.id and value[]")
            elif not (item.get("settings") or {}).get("__type"):
                errors.append("each postiz post needs settings.__type")
    return errors


def _body(request: dict) -> dict:
    return {"type": "schedule", "date": request["date"], "shortLink": bool(request.get("shortLink", False)),
            "tags": request.get("tags", []), "posts": request["posts"]}


def describe(request: dict, approval: dict) -> list[dict]:
    return [{"method": "POST", "url": "{POSTIZ_BASE_URL}/public/v1/posts", "body": _body(request)}]


def run(request: dict, approval: dict, *, http, secret) -> dict:
    base = require_secret(secret, "POSTIZ_BASE_URL").rstrip("/")
    key = require_secret(secret, "POSTIZ_API_KEY")
    response = http("POST", f"{base}/public/v1/posts", {"Authorization": key}, _body(request))
    return {"status": "scheduled", "provider_ids": {"post_ids": first_id(response, "postId", "id")}}
