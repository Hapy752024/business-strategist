#!/usr/bin/env python3
"""Generate a matched illustration/photo style-frame pair via FAL edit models.

Uses a public reference image (e.g. Wikimedia Commons) so scenery is authentic,
then produces (1) a warm-filmic photo layer and (2) a line-art illustration
layer with the same composition (required for "The Reveal" hover crossfade).

Calls the synchronous fal.run endpoint and downloads results immediately.
Records provenance (prompts, reference URL, model) to a JSON record.
"""

from __future__ import annotations

import argparse
import hashlib
import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fal_assets import download_assets, now_iso  # noqa: E402

SYNC_BASE = "https://fal.run"


def call_fal(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
    key = os.environ.get("FAL_AI_API_KEY")
    if not key:
        raise RuntimeError("FAL_AI_API_KEY is required")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SYNC_BASE}/{endpoint}",
        data=body,
        headers={
            "Authorization": f"Key {key}",
            "Content-Type": "application/json",
            "X-Fal-Store-IO": "0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoint", default="fal-ai/nano-banana-pro/edit")
    ap.add_argument("--reference-file", type=Path, required=True, help="local path to the authentic reference photo (sent as base64 data URI; public URLs are unreliable via FAL)")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--aspect-ratio", default="21:9")
    ap.add_argument("--resolution", default="1K", choices=["1K", "2K", "4K"])
    ap.add_argument("--label", required=True, help="asset label, e.g. hero-lake-como-photo")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--record", type=Path)
    args = ap.parse_args()

    mime = "image/png" if args.reference_file.suffix.lower() == ".png" else "image/jpeg"
    reference = base64.b64encode(args.reference_file.read_bytes()).decode()
    uri = f"data:{mime};base64,{reference}"
    payload: dict[str, object] = {
        "prompt": args.prompt,
        "image_urls": [uri],
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "num_images": 1,
    }
    result = call_fal(args.endpoint, payload)
    records = download_assets(result, args.output_dir)

    provenance = {
        "label": args.label,
        "model": args.endpoint,
        "prompt": args.prompt,
        "reference_file": args.reference_file.as_posix(),
        "reference_sha256": hashlib.sha256(args.reference_file.read_bytes()).hexdigest(),
        "aspect_ratio": args.aspect_ratio,
        "generated_at": now_iso(),
        "assets": records,
    }
    if args.record:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
