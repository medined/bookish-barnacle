#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$ROOT_DIR")"
PROJECT_NAME="$(basename "$ROOT_DIR")"
BACKUP_FILE="$BACKUP_DIR/${PROJECT_NAME}-$(date +%Y%m%d-%Hh%Mm).tar.gz"

if ! mkdir -p "$BACKUP_DIR" 2>/dev/null || ! touch "${BACKUP_FILE}.tmp" 2>/dev/null; then
  BACKUP_DIR="$ROOT_DIR/backups"
  mkdir -p "$BACKUP_DIR"
  BACKUP_FILE="$BACKUP_DIR/${PROJECT_NAME}-$(date +%Y%m%d-%Hh%Mm).tar.gz"
  echo "Default backup directory not writable; using $BACKUP_DIR instead."
else
  rm -f "${BACKUP_FILE}.tmp"
fi

echo "Creating backup at $BACKUP_FILE"

BACKUP_EXCLUDES=(
  "__marimo__"
  "__pycache__"
  ".cache"
  ".pytest_cache"
  ".ruff_cache"
  ".uv-cache"
  ".venv"
  "app/static/published"
  "backups"
  "html"
  "json"
)

BACKUP_EXCLUDE_STR="$(printf '%s:' "${BACKUP_EXCLUDES[@]}")"
BACKUP_EXCLUDE_STR="${BACKUP_EXCLUDE_STR%:}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

ROOT_DIR="$ROOT_DIR" BACKUP_FILE="$BACKUP_FILE" BACKUP_EXCLUDE="$BACKUP_EXCLUDE_STR" "$PYTHON_BIN" <<'PY'
import os
import tarfile
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
backup_file = Path(os.environ["BACKUP_FILE"])
excludes = [entry for entry in os.environ.get("BACKUP_EXCLUDE", "").split(":") if entry]

def should_skip(relative: Path) -> bool:
    relative_posix = relative.as_posix()
    for prefix in excludes:
        if relative_posix == prefix or relative_posix.startswith(prefix + "/"):
            return True
    return False

with tarfile.open(backup_file, "w:gz") as archive:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not relative.parts:
            continue
        if should_skip(relative):
            continue
        archive.add(path, arcname=relative.as_posix())
PY

echo "Backup created at $BACKUP_FILE"
