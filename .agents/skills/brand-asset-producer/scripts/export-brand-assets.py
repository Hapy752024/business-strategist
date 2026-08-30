#!/usr/bin/env python3
"""Export SVG brand masters to common logo/favicon formats."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

PNG_SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]


def run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def export_with_inkscape(svg: Path, out_dir: Path, sizes: list[int], eps: bool) -> list[dict]:
    records = []
    inkscape = shutil.which("inkscape")
    if not inkscape:
        return records
    for size in sizes:
        out = out_dir / f"{svg.stem}-{size}.png"
        ok = run([inkscape, str(svg), "--export-type=png", f"--export-filename={out}", f"--export-width={size}", f"--export-height={size}"])
        if ok and out.exists() and out.stat().st_size > 0:
            records.append({"source": str(svg), "file": str(out), "type": "png", "size": size})
    if eps:
        out = out_dir / f"{svg.stem}.eps"
        ok = run([inkscape, str(svg), "--export-type=eps", f"--export-filename={out}"])
        if ok and out.exists() and out.stat().st_size > 0:
            records.append({"source": str(svg), "file": str(out), "type": "eps"})
    return records


def export_with_cairosvg(svg: Path, out_dir: Path, sizes: list[int]) -> list[dict]:
    records = []
    try:
        import cairosvg  # type: ignore
    except ImportError:
        return records
    for size in sizes:
        out = out_dir / f"{svg.stem}-{size}.png"
        try:
            cairosvg.svg2png(url=str(svg), write_to=str(out), output_width=size, output_height=size)
        except Exception:
            continue
        if out.exists() and out.stat().st_size > 0:
            records.append({"source": str(svg), "file": str(out), "type": "png", "size": size})
    return records


def build_ico(out_dir: Path, stem: str) -> dict | None:
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        Image = None

    pngs = [out_dir / f"{stem}-{size}.png" for size in [16, 32, 48, 64, 128, 256]]
    existing_paths = [path for path in pngs if path.exists() and path.stat().st_size > 0]
    out = out_dir / f"{stem}.ico"

    if Image and existing_paths:
        images = [Image.open(path) for path in existing_paths]
        images[0].save(out, format="ICO", sizes=[image.size for image in images])
        if out.exists() and out.stat().st_size > 0:
            return {"file": str(out), "type": "ico", "sources": [str(path) for path in existing_paths]}

    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        return None
    existing = [str(path) for path in existing_paths]
    if not existing:
        return None
    if run([magick, *existing, str(out)]) and out.exists() and out.stat().st_size > 0:
        return {"file": str(out), "type": "ico", "sources": existing}
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("svg_dir", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--eps", action="store_true")
    parser.add_argument("--sizes", default=",".join(str(size) for size in PNG_SIZES))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    sizes = [int(size.strip()) for size in args.sizes.split(",") if size.strip()]
    manifest = []
    for svg in sorted(args.svg_dir.glob("*.svg")):
        before = len(manifest)
        manifest.extend(export_with_inkscape(svg, args.out_dir, sizes, args.eps))
        if len(manifest) == before:
            manifest.extend(export_with_cairosvg(svg, args.out_dir, sizes))
        ico = build_ico(args.out_dir, svg.stem)
        if ico:
            manifest.append({"source": str(svg), **ico})
    manifest_path = args.out_dir / "export-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exported": len(manifest), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
