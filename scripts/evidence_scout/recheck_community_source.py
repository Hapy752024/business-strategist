#!/usr/bin/env python3
"""Perform a one-URL metadata recheck and emit a discovery-role attestation."""

from __future__ import annotations

import argparse, base64, hashlib, json, os, re, sys, urllib.parse, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate_apis"))
from common import http_get  # noqa: E402


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def response_text(response: dict[str, Any]) -> str:
    body = response.get("body")
    if isinstance(body, dict) and isinstance(body.get("text"), str):
        return body["text"]
    return json.dumps(body, ensure_ascii=False) if body is not None else ""


def has_recent_timestamp(text: str, now: datetime | None = None) -> bool:
    """Accept timestamps attached to structured post/thread fields, not loose page words."""
    now = now or datetime.now(timezone.utc); lowered = text.casefold()
    structured = []
    patterns = (
        r'(?:"(?:created_time|creation_time|publish_time|published_at|timestamp)"|datetime)\s*[:=]\s*["\']?([^"\'<>\s,}]+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
    )
    for pattern in patterns:
        structured.extend(re.findall(pattern, lowered))
    for raw in structured:
        if re.fullmatch(r"1\d{9}(?:\d{3})?", raw):
            stamp = int(raw[:10])
            if timedelta(0) <= now - datetime.fromtimestamp(stamp, tz=timezone.utc) <= timedelta(days=30): return True
        normalized = raw[:10]
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                observed = datetime.strptime(normalized, fmt).replace(tzinfo=timezone.utc)
                if timedelta(0) <= now - observed <= timedelta(days=30): return True
            except ValueError: pass
    return False


def semantic_assessment(url: str, response: dict[str, Any]) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(url); host = (parsed.hostname or "").casefold(); path = parsed.path.casefold()
    text = response_text(response); lowered = text.casefold()
    headers = response.get("headers") if isinstance(response.get("headers"), dict) else {}
    content_type = str(next((value for key, value in headers.items() if str(key).casefold() == "content-type"), "")).split(";", 1)[0].casefold()
    body_size = int(response.get("body_size_bytes") or len(text.encode("utf-8")))
    login_markers = ("log in", "login", "checkpoint", "sign in", "connexion", "se connecter", "anmelden", "iniciar sesión", "iniciar sesion", "accedi", "entrar para continuar", "iniciar sessão", "iniciar sessao", "security check", "تسجيل الدخول")
    final_path = urllib.parse.urlsplit(str(response.get("final_url") or url)).path.casefold()
    login_wall = any(marker in lowered for marker in login_markers) or final_path.startswith(("/login", "/checkpoint")) or bool(re.search(r'<input[^>]+type=["\']password', lowered))
    textual = not content_type or any(kind in content_type for kind in ("html", "json", "text"))
    public_content = bool(response.get("ok") and response.get("status_code") == 200 and textual and body_size >= 100 and not login_wall)
    facebook = host in {"facebook.com", "www.facebook.com", "m.facebook.com"}
    group_match = re.fullmatch(r"/groups/([^/?#]+)/?", path)
    reserved_groups = {"feed", "discover", "joins", "create", "groups", "notifications"}
    group_id_marker = bool(re.search(r'"(?:group_id|groupid)"\s*:\s*"?[a-z0-9._-]+', lowered))
    requested_slug = group_match.group(1) if group_match else ""
    page_id_marker = bool(re.search(r'"(?:page_id|pageid)"\s*:\s*"?\d{3,}', lowered))
    page_shape_marker = any(marker in lowered for marker in ('"is_business_page":true', '"page_category"', '"page_type"'))
    target_marker = bool(path.strip("/") and path.strip("/") in lowered)
    if facebook and group_match and requested_slug not in reserved_groups and group_id_marker:
        observed_entity = "facebook_group"
    elif facebook and path.strip("/") and not path.startswith(("/login", "/share", "/sharer", "/watch", "/help", "/privacy", "/profile.php", "/groups")) and page_id_marker and page_shape_marker and target_marker:
        observed_entity = "facebook_page"
    elif not facebook and any(marker in lowered for marker in ("forum", "discussion", "thread", "topic", "reply", "replies")):
        observed_entity = "forum"
    else:
        observed_entity = "unresolved"
    interaction = bool(re.search(r'"(?:post_id|story_fbid|thread_id|topic_id)"\s*:', lowered) or "<article" in lowered)
    recent = has_recent_timestamp(lowered)
    markers = (["login_or_challenge"] if login_wall else []) + (["interaction"] if interaction else []) + (["recent_time"] if recent else [])
    return {"content_type": content_type or "unknown", "body_size_bytes": body_size, "access_status": "public_content" if public_content else "not_verified_public", "entity_type_observed": observed_entity, "activity_status": "active_recent" if public_content and interaction and recent else "not_verified_active", "semantic_markers": markers}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a signed metadata-only direct community recheck.")
    parser.add_argument("--url", required=True); parser.add_argument("--entity-type", choices=("forum", "facebook_group", "facebook_page"), required=True); parser.add_argument("--out", required=True)
    args = parser.parse_args(); parsed = urllib.parse.urlsplit(args.url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname: parser.error("--url must be an absolute HTTP(S) URL")
    private_b64 = os.environ.get("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64", "")
    try: private = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_b64))
    except Exception as exc: raise SystemExit("COMMUNITY_DISCOVERY_PRIVATE_KEY_B64 must contain a base64-encoded 32-byte Ed25519 private key.") from exc
    response = http_get(args.url); body_digest = hashlib.sha256(canonical(response.get("body"))).hexdigest(); observed = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    public_raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    semantic = semantic_assessment(args.url, response)
    requested = args.entity_type; observed_entity = semantic["entity_type_observed"]
    status = "retrieved" if response.get("ok") and requested == observed_entity else "failed"
    receipt = {"artifact_type": "community_direct_recheck", "schema_version": 2, "recheck_id": str(uuid.uuid4()), "url": args.url.rstrip("/"), "locator": args.url, "final_url": str(response.get("final_url") or args.url).rstrip("/"), "entity_type": requested, "provider": "direct_http", "http_status": response.get("status_code"), "status": status, "observed_at": observed, "content_digest": body_digest, "response_body_retained": False, **semantic, "signature_algorithm": "ed25519", "key_id": hashlib.sha256(public_raw).hexdigest()}
    receipt["signature"] = base64.b64encode(private.sign(canonical(receipt))).decode(); target = Path(args.out); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "http_status": receipt["http_status"], "access_status": receipt["access_status"], "entity_type_observed": receipt["entity_type_observed"], "activity_status": receipt["activity_status"], "output": str(target)})); return 0 if status == "retrieved" else 1


if __name__ == "__main__": raise SystemExit(main())
