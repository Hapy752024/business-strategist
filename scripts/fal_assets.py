#!/usr/bin/env python3
"""Approval-gated build-time FAL queue adapter.

The default action is a redacted dry run. It never prints the credential and
does not submit a paid request unless both --execute and --confirm are given.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import tempfile
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path


ENDPOINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")
ALLOWED_MEDIA_HOSTS = ("fal.media", "fal.ai")
MAX_ASSET_BYTES = 25 * 1024 * 1024


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_request(args: argparse.Namespace) -> dict[str, object]:
    if not ENDPOINT_RE.fullmatch(args.endpoint):
        raise ValueError("endpoint must be a model path, not a URL")
    if args.variants < 1 or args.variants > 20:
        raise ValueError("variants must be between 1 and 20")
    if args.max_cost < args.estimated_cost:
        raise ValueError("max-cost must cover estimated-cost")
    if args.width < 1 or args.height < 1 or args.width > 8192 or args.height > 8192:
        raise ValueError("dimensions must be between 1 and 8192 pixels")
    return {
        "endpoint": args.endpoint,
        "prompt": args.prompt,
        "negative_prompt": args.negative_prompt,
        "variants": args.variants,
        "width": args.width,
        "height": args.height,
        "seed": args.seed,
        "estimated_cost": args.estimated_cost,
        "max_cost": args.max_cost,
        "approval_id": args.approval_id,
        "generated_at": now_iso(),
        "retention_seconds": args.retention_seconds,
        "store_io": False,
    }


def submit(request: dict[str, object]) -> dict[str, object]:
    key = os.environ.get("FAL_AI_API_KEY")
    if not key:
        raise RuntimeError("FAL_AI_API_KEY is required only for an approved execute")
    endpoint = str(request["endpoint"])
    payload = {"prompt": request["prompt"], "negative_prompt": request["negative_prompt"], "num_images": request["variants"], "image_size": {"width": request["width"], "height": request["height"]}}
    if request.get("seed") is not None:
        payload["seed"] = request["seed"]
    body = json.dumps(payload).encode("utf-8")
    lifecycle = json.dumps({"expiration_duration_seconds": request["retention_seconds"]})
    http_request = urllib.request.Request(
        f"https://queue.fal.run/{endpoint}",
        data=body,
        headers={
            "Authorization": f"Key {key}",
            "Content-Type": "application/json",
            "X-Fal-Store-IO": "0",
            "X-Fal-Object-Lifecycle-Preference": lifecycle,
        },
        method="POST",
    )
    with urllib.request.urlopen(http_request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    # Keep the record useful without retaining arbitrary provider payloads.
    return {"request_id": data.get("request_id"), "gateway_request_id": data.get("gateway_request_id"), "response_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}


def extract_media_urls(value: object) -> list[str]:
    """Extract FAL output URLs without retaining an arbitrary provider payload."""
    found: list[str] = []
    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str):
            found.append(url)
        for child in value.values():
            found.extend(extract_media_urls(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(extract_media_urls(child))
    return list(dict.fromkeys(found))


def safe_media_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_MEDIA_HOSTS):
        raise ValueError(f"refusing untrusted media URL host: {host or '<missing>'}")
    if parsed.username or parsed.password:
        raise ValueError("media URL must not contain credentials")
    return host, parsed.path


def image_metadata(content: bytes) -> tuple[str, str, int, int]:
    if content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) >= 24:
        width, height = struct.unpack(">II", content[16:24])
        return "image/png", ".png", width, height
    if content.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(content):
            if content[offset] != 0xFF:
                offset += 1
                continue
            marker = content[offset + 1]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", content[offset + 5:offset + 9])
                return "image/jpeg", ".jpg", width, height
            if marker in {0xD8, 0xD9}:
                offset += 2
                continue
            length = struct.unpack(">H", content[offset + 2:offset + 4])[0]
            offset += 2 + length
    raise ValueError("unsupported or malformed image; only validated PNG/JPEG assets are accepted")


def download_assets(
    payload: object,
    output_dir: Path,
    *,
    expected_width: int | None = None,
    expected_height: int | None = None,
    opener=urllib.request.urlopen,
) -> list[dict[str, object]]:
    """Immediately download temporary FAL URLs and return URL-free asset records."""
    urls = extract_media_urls(payload)
    if not urls:
        raise ValueError("provider response contains no media URLs")
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for index, url in enumerate(urls, start=1):
        host, _ = safe_media_url(url)
        request = urllib.request.Request(url, headers={"User-Agent": "business-strategist-fal-finalizer/1.0"})
        with opener(request, timeout=30) as response:
            final_url = response.geturl() if hasattr(response, "geturl") else url
            safe_media_url(final_url)
            content = response.read(MAX_ASSET_BYTES + 1)
            declared = str(response.headers.get("Content-Type", "")).split(";", 1)[0].lower()
        if len(content) > MAX_ASSET_BYTES:
            raise ValueError(f"asset {index} exceeds {MAX_ASSET_BYTES} bytes")
        mime, suffix, width, height = image_metadata(content)
        if declared and declared not in {mime, "application/octet-stream"}:
            raise ValueError(f"asset {index} MIME mismatch: declared {declared}, detected {mime}")
        if expected_width is not None and width != expected_width:
            raise ValueError(f"asset {index} width mismatch: expected {expected_width}, found {width}")
        if expected_height is not None and height != expected_height:
            raise ValueError(f"asset {index} height mismatch: expected {expected_height}, found {height}")
        sha = hashlib.sha256(content).hexdigest()
        destination = output_dir / f"fal-{index:02d}-{sha[:12]}{suffix}"
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
            raise ValueError(f"destination conflict: {destination}")
        if not destination.exists():
            fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=output_dir)
            os.close(fd)
            temporary = Path(temporary_name)
            try:
                temporary.write_bytes(content)
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
        records.append({
            "path": destination.as_posix(),
            "sha256": sha,
            "bytes": len(content),
            "mime_type": mime,
            "width": width,
            "height": height,
            "source_provider": "fal",
            "source_host": host,
            "remote_url_sha256": hashlib.sha256(url.encode()).hexdigest(),
            "downloaded_at": now_iso(),
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--variants", type=int, default=1)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--estimated-cost", type=float, required=True)
    parser.add_argument("--max-cost", type=float, required=True)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--retention-seconds", type=int, default=3600)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    request = build_request(args)
    result: dict[str, object] = {"mode": "dry_run", "request": request}
    if args.execute:
        if not args.confirm:
            raise SystemExit("refusing paid FAL request without --confirm")
        result["mode"] = "submitted"
        result["provider"] = submit(request)
    if args.record:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
