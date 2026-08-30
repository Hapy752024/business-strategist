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
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ENDPOINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")


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
