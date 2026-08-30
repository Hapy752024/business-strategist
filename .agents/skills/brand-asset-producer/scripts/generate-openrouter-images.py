#!/usr/bin/env python3
"""Generate brand concept images through OpenRouter using stdlib only."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80] or "image"


def decode_data_url(data_url: str) -> tuple[str, bytes]:
    if not data_url.startswith("data:") or "," not in data_url:
        raise ValueError("Expected base64 data URL")
    header, payload = data_url.split(",", 1)
    mime = header.split(";", 1)[0].removeprefix("data:")
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/svg+xml": "svg"}.get(mime, "bin")
    return ext, base64.b64decode(payload)


def request_image(base_url: str, api_key: str, model: str, prompt: str, app_name: str, site_url: str | None) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": app_name,
    }
    if site_url:
        headers["HTTP-Referer"] = site_url
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_image_urls(response: dict) -> list[str]:
    urls = []
    for choice in response.get("choices", []):
        message = choice.get("message", {})
        for image in message.get("images", []) or []:
            image_url = image.get("image_url") or image.get("imageUrl") or {}
            url = image_url.get("url") if isinstance(image_url, dict) else None
            if url:
                urls.append(url)
    return urls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("brand/generated-images"))
    parser.add_argument("--models", default=os.environ.get("OPENROUTER_IMAGE_MODELS", ""))
    parser.add_argument("--alternatives", type=int, default=int(os.environ.get("OPENROUTER_IMAGE_ALTERNATIVES", "1")))
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()

    load_env_file(args.env_file)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    app_name = os.environ.get("OPENROUTER_APP_NAME", "brand-designer")
    site_url = os.environ.get("OPENROUTER_SITE_URL") or None
    models = [model.strip() for model in args.models.split(",") if model.strip()]
    if not models:
        raise SystemExit("No image models configured")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for model in models:
        for index in range(args.alternatives):
            try:
                response = request_image(base_url, api_key, model, args.prompt, app_name, site_url)
                urls = extract_image_urls(response)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
                manifest.append({"model": model, "alternative": index + 1, "error": str(exc)})
                continue
            for image_number, data_url in enumerate(urls, start=1):
                ext, data = decode_data_url(data_url)
                filename = f"{slugify(model)}-{int(time.time())}-{index + 1}-{image_number}.{ext}"
                path = args.out_dir / filename
                path.write_bytes(data)
                manifest.append({"model": model, "alternative": index + 1, "file": str(path), "format": ext})

    manifest_path = args.out_dir / "openrouter-image-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    generated = len([item for item in manifest if "file" in item])
    print(json.dumps({"generated": generated, "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
