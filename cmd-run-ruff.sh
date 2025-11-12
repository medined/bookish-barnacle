#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v ruff >/dev/null 2>&1; then
    echo "ruff is not installed. Install it with 'uv tool install ruff' or 'pip install ruff'." >&2
    exit 1
fi

exec ruff check "$ROOT_DIR" "$@"
