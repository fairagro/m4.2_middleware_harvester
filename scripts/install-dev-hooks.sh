#!/usr/bin/env bash
# Product-local glue until Devinfra owns shell/hook repair end-to-end
# (m4.2_middleware_devinfra#56, #58). Not a synced script.
#
# Calls:
#   - scripts/uv-sync-dev.sh          (product: --dev --all-packages + stale venv)
#   - pre-commit install              (commit-stage)
#   - scripts/setup-git-hooks.sh      (synced: pre-push only; no Git LFS)
#
# Prefer postCreate for first install; run this manually after path/venv drift.
# Do not invoke from load-env.sh (per-shell) — that belongs in a shared shell-init
# design if Devinfra wants it at all.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
venv_python="${repo_root}/.venv/bin/python"

_venv_usable() {
  [ -x "$venv_python" ] && "$venv_python" -c 'pass' 2>/dev/null \
    && "$venv_python" -m pre_commit --version &>/dev/null
}

if ! _venv_usable; then
  echo "Repairing .venv (Python interpreter missing or host paths stale)..."
  bash "${script_dir}/uv-sync-dev.sh"
fi

if ! _venv_usable; then
  echo "WARNING: pre-commit unavailable — run: bash scripts/uv-sync-dev.sh" >&2
  exit 1
fi

export PATH="${repo_root}/.venv/bin:${PATH}"

git_hooks_dir="$(git -C "${repo_root}" rev-parse --git-path hooks 2>/dev/null || echo ".git/hooks")"
[[ "$git_hooks_dir" = /* ]] || git_hooks_dir="${repo_root}/${git_hooks_dir}"
hook="${git_hooks_dir}/pre-commit"
if [ ! -f "$hook" ] || ! grep -Fq "INSTALL_PYTHON=${venv_python}" "$hook" 2>/dev/null; then
  echo "Installing pre-commit hooks..."
  (cd "${repo_root}" && "${venv_python}" -m pre_commit install --hook-type pre-commit)
else
  echo "pre-commit hook up to date"
fi

bash "${script_dir}/setup-git-hooks.sh"

echo "Dev hooks installed"
