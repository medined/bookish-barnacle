#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYPROJECT="${ROOT_DIR}/pyproject.toml"
CACHE_ROOT="${ROOT_DIR}/.cache/uv"

if [[ -z "${UV_CACHE_DIR:-}" ]]; then
    export UV_CACHE_DIR="${CACHE_ROOT}"
fi

mkdir -p "${UV_CACHE_DIR}"

run_pytest_cmd() {
    if "$@"; then
        return 0
    fi
    status=$?
    if [[ $status -eq 5 ]]; then
        return 0
    fi
    return $status
}

if [[ -f "$PYPROJECT" ]]; then
    if command -v rg >/dev/null 2>&1; then
        if rg --fixed-strings --quiet "[tool.uv.dependency-groups]" "$PYPROJECT"; then
            if run_pytest_cmd uv run --group test pytest "$@"; then
                exit 0
            fi
        fi
    elif grep -Fq "[tool.uv.dependency-groups]" "$PYPROJECT"; then
        if run_pytest_cmd uv run --group test pytest "$@"; then
            exit 0
        fi
    fi
fi

if run_pytest_cmd uv run pytest "$@"; then
    exit 0
fi

if command -v uvx >/dev/null 2>&1; then
    if run_pytest_cmd uvx pytest "$@"; then
        exit 0
    fi
fi

if command -v pytest >/dev/null 2>&1; then
    if run_pytest_cmd pytest "$@"; then
        exit 0
    fi
fi

echo "pytest is not available. Install it (e.g. 'uv tool install pytest' or add it to your environment)." >&2
exit 1
