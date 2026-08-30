#!/usr/bin/env python3
"""Install or print commands for brand export tooling."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import venv
from pathlib import Path


ROOT = Path.cwd()
VENV = ROOT / ".brand-tools" / "venv"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")


def system_commands() -> list[str]:
    system = platform.system()
    if system == "Darwin":
        return ["brew install --cask inkscape", "brew install imagemagick"]
    if system == "Windows":
        return ["winget install Inkscape.Inkscape", "winget install ImageMagick.ImageMagick"]
    return [
        "sudo apt-get update",
        "sudo apt-get install -y inkscape imagemagick python3-pip python3-venv",
    ]


def install_temp() -> dict:
    VENV.parent.mkdir(parents=True, exist_ok=True)
    if not venv_python().exists():
        venv.EnvBuilder(with_pip=True).create(VENV)
    python = venv_python()
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "pillow", "cairosvg"], check=True)
    return {
        "venv": str(VENV),
        "python": str(python),
        "installed": ["pillow", "cairosvg"],
        "note": "Temporary Python fallback covers PNG/PDF/ICO-style workflows; EPS fidelity still needs Inkscape.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["temp", "system"], required=True)
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()

    if args.mode == "system":
        print(json.dumps({
            "platform": platform.system(),
            "commands": system_commands(),
            "note": "Ask the user before running system install commands.",
        }, indent=2))
        return 0

    if args.print_only:
        print(json.dumps({
            "platform": platform.system(),
            "commands": [
                "python3 -m venv .brand-tools/venv",
                ".brand-tools/venv/bin/python -m pip install --upgrade pip",
                ".brand-tools/venv/bin/python -m pip install pillow cairosvg",
            ],
            "windows_commands": [
                "py -m venv .brand-tools\\venv",
                ".brand-tools\\venv\\Scripts\\python.exe -m pip install --upgrade pip",
                ".brand-tools\\venv\\Scripts\\python.exe -m pip install pillow cairosvg",
            ],
        }, indent=2))
        return 0

    print(json.dumps(install_temp(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
