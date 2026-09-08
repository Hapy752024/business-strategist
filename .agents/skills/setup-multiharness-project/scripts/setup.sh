#!/usr/bin/env bash
# Thin entrypoint; all target operations use the trusted bundled implementation.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 -I -B "$SCRIPT_DIR/setup_core.py" "$@"
