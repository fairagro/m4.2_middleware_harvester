#!/usr/bin/env bash
# Dev dependency sync for devcontainer postCreate and local use.
# Drops a stale .venv when its Python interpreter or script shebangs are broken
# (common after devcontainer rebuild or workspace path changes).

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

_venv_script_shebang_stale() {
    local script="${1:?script path required}"
    [ ! -f "$script" ] && return 1
    local shebang
    shebang=$(head -1 "$script" | sed 's/^#!//')
    [ -n "$shebang" ] && [ ! -x "$shebang" ]
}

_venv_stale() {
    [ ! -d .venv/bin ] && return 1
    if ! .venv/bin/python -c 'import sys' &>/dev/null; then
        return 0
    fi
    _venv_script_shebang_stale .venv/bin/pre-commit
}

if _venv_stale; then
    echo "Removing stale .venv (broken Python interpreter or script shebangs)..."
    rm -rf .venv
fi

exec uv sync --dev --all-packages
