#!/usr/bin/env python3
"""Run the Firecrawl CLI with this project's required account binding."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "validate_apis"))
from common import get_secret


def main() -> int:
    name, secret = get_secret("FIRECRAWL_API_KEY_HGINVESTOR")
    if name != "FIRECRAWL_API_KEY_HGINVESTOR" or not secret:
        print("FIRECRAWL_API_KEY_HGINVESTOR is required for this project", file=sys.stderr)
        return 2
    environment = os.environ.copy()
    environment["FIRECRAWL_API_KEY"] = secret
    return subprocess.run(["firecrawl", *sys.argv[1:]], env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
