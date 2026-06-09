#!/usr/bin/env bash
# Dev setup: repair .venv if needed, install pre-commit + Git LFS hooks.
# Used from devcontainer postCreate and load-env.sh when the venv/hooks are stale.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
venv_python="${repo_root}/.venv/bin/python"

_venv_usable() {
    [ -x "$venv_python" ] && "$venv_python" -c 'pass' 2>/dev/null
}

if ! _venv_usable; then
    echo "🔧 Repairing .venv (Python interpreter missing or host paths stale)..."
    bash "${script_dir}/uv-sync-dev.sh"
fi

if ! _venv_usable; then
    echo "⚠️ pre-commit unavailable — run: bash scripts/uv-sync-dev.sh" >&2
    exit 1
fi

export PATH="${repo_root}/.venv/bin:${PATH}"

git_hooks_dir="$(git -C "${repo_root}" rev-parse --git-path hooks 2>/dev/null || echo ".git/hooks")"
[[ "$git_hooks_dir" = /* ]] || git_hooks_dir="${repo_root}/${git_hooks_dir}"
hook="${git_hooks_dir}/pre-commit"
if [ ! -f "$hook" ] || ! grep -Fq "INSTALL_PYTHON=${venv_python}" "$hook" 2>/dev/null; then
    echo "🔧 Installing pre-commit hooks..."
    (cd "${repo_root}" && uv run pre-commit install --hook-type pre-commit)
else
    echo "✅ pre-commit hook up to date"
fi

echo "🔧 Setting up Git LFS hooks..."
bash "${script_dir}/setup-git-lfs.sh"

echo "✅ Dev hooks installed"
