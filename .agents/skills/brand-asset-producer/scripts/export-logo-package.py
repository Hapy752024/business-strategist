#!/usr/bin/env python3
"""Export approved SVG logo masters into canonical PNG/ICO/PDF/EPS folders."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SMALL_SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]
WORDMARK_SIZES = [512, 1024, 2048]


def run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def is_wordmark(svg: Path) -> bool:
    return svg.stem.startswith("wordmark")


def is_square(svg: Path) -> bool:
    """True when the SVG canvas is square (marks/favicons); False for wide wordmarks.

    Exporting a wide wordmark with forced square pixel dimensions produces a
    huge square canvas with the artwork floating in a corner. Non-square SVGs
    must be exported with width only so the aspect ratio is preserved.
    """
    import re
    try:
        head = svg.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        return True
    match = re.search(r'<svg[^>]*\bwidth="([0-9.]+)"[^>]*\bheight="([0-9.]+)"', head)
    if match:
        width, height = float(match.group(1)), float(match.group(2))
    else:
        viewbox = re.search(r'viewBox="[0-9.\s-]+\s([0-9.]+)\s([0-9.]+)"', head)
        if not viewbox:
            return True
        width, height = float(viewbox.group(1)), float(viewbox.group(2))
    return abs(width - height) < 1.0


def export_png(svg: Path, out_dir: Path, sizes: list[int]) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    inkscape = shutil.which("inkscape")
    square = is_square(svg)
    for size in sizes:
        out = out_dir / f"{svg.stem}-{size}.png"
        ok = False
        if inkscape:
            if square:
                ok = run([inkscape, str(svg), "--export-type=png", f"--export-filename={out}", f"--export-width={size}", f"--export-height={size}"])
            else:
                # Non-square (wordmark): width only, keep the natural aspect ratio
                ok = run([inkscape, str(svg), "--export-type=png", f"--export-filename={out}", f"--export-width={size}"])
        if not ok:
            try:
                import cairosvg  # type: ignore
                if square:
                    cairosvg.svg2png(url=str(svg), write_to=str(out), output_width=size, output_height=size)
                else:
                    cairosvg.svg2png(url=str(svg), write_to=str(out), output_width=size)
                ok = True
            except Exception:
                ok = False
        if ok and out.exists() and out.stat().st_size > 0:
            records.append({"source": str(svg), "file": str(out), "type": "png", "size": size})
    return records


def export_vector(svg: Path, out_dir: Path, export_type: str) -> dict | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    inkscape = shutil.which("inkscape")
    if not inkscape:
        return None
    out = out_dir / f"{svg.stem}.{export_type}"
    if run([inkscape, str(svg), f"--export-type={export_type}", f"--export-filename={out}"]) and out.exists() and out.stat().st_size > 0:
        return {"source": str(svg), "file": str(out), "type": export_type}
    return None


def build_ico(svg: Path, out_dir: Path, stem: str) -> dict | None:
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return None

    paths = [out_dir / f"{stem}-{size}.png" for size in [16, 32, 48, 64, 128, 256]]
    existing = [path for path in paths if path.exists() and path.stat().st_size > 0]
    if not existing:
        return None
    out = out_dir / f"{stem}.ico"
    images = [Image.open(path) for path in existing]
    images[0].save(out, format="ICO", sizes=[image.size for image in images])
    if out.exists() and out.stat().st_size > 0:
        return {"source": str(svg), "file": str(out), "type": "ico", "sources": [str(path) for path in existing]}
    return None


def write_manifest(out_dir: Path, records: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "export-manifest.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def check_exports(source_dir: Path, export_dir: Path) -> int:
    """Validate export manifests: canonical provenance, presence, freshness.

    Fails when a manifest record points at a source outside source_dir (e.g. a
    /tmp staging copy), when a recorded export is missing, or when an export is
    older than its source (stale after a logo edit).
    """
    errors: list[str] = []
    source_root = source_dir.resolve()
    for name in ("wordmark", "small", "pdf", "eps"):
        manifest_path = export_dir / name / "export-manifest.json"
        if not manifest_path.exists():
            errors.append(f"missing manifest: {manifest_path}")
            continue
        try:
            records = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid manifest JSON {manifest_path}: {exc}")
            continue
        for record in records:
            source = Path(record.get("source", ""))
            if not source.is_absolute():
                source = Path.cwd() / source
            try:
                source.resolve().relative_to(source_root)
            except ValueError:
                errors.append(f"{name}: non-canonical source {record.get('source')} (expected inside {source_dir})")
                continue
            export_file = Path(record.get("file", ""))
            if not export_file.is_absolute():
                export_file = Path.cwd() / export_file
            if not export_file.exists():
                errors.append(f"{name}: missing export {record.get('file')}")
                continue
            if source.exists() and export_file.stat().st_mtime < source.stat().st_mtime:
                errors.append(f"{name}: stale export {record.get('file')} older than {record.get('source')}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"check OK: manifests in {export_dir} are canonical, present, and fresh")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("export_dir", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate manifests (provenance, presence, freshness) instead of exporting")
    args = parser.parse_args()

    if args.check:
        return check_exports(args.source_dir, args.export_dir)

    svgs = sorted(args.source_dir.glob("*.svg"))
    if not svgs:
        raise SystemExit(f"no SVG files found in {args.source_dir}")

    wordmark_records: list[dict] = []
    small_records: list[dict] = []
    pdf_records: list[dict] = []
    eps_records: list[dict] = []

    for svg in svgs:
        if is_wordmark(svg):
            wordmark_records.extend(export_png(svg, args.export_dir / "wordmark", WORDMARK_SIZES))
        else:
            small_records.extend(export_png(svg, args.export_dir / "small", SMALL_SIZES))
            ico = build_ico(svg, args.export_dir / "small", svg.stem)
            if ico:
                small_records.append({"source": str(svg), **ico})
        pdf = export_vector(svg, args.export_dir / "pdf", "pdf")
        eps = export_vector(svg, args.export_dir / "eps", "eps")
        if pdf:
            pdf_records.append(pdf)
        if eps:
            eps_records.append(eps)

    write_manifest(args.export_dir / "wordmark", wordmark_records)
    write_manifest(args.export_dir / "small", small_records)
    write_manifest(args.export_dir / "pdf", pdf_records)
    write_manifest(args.export_dir / "eps", eps_records)
    print(json.dumps({
        "wordmark": len(wordmark_records),
        "small": len(small_records),
        "pdf": len(pdf_records),
        "eps": len(eps_records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
