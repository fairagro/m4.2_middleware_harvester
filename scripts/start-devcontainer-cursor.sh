#!/usr/bin/env bash
#
# Open this repository in a Dev Container via DevPod + Cursor.
#
# Cursor has no built-in "Reopen in Container" (unlike VS Code). DevPod builds
# the devcontainer and connects Cursor over SSH — equivalent to VS Code's flow,
# where load-env.sh runs inside the container after it starts (via postCreateCommand).
#
# Usage:
#   ./scripts/start-devcontainer-cursor.sh
#   ./scripts/start-devcontainer-cursor.sh --recreate
#   ./scripts/start-devcontainer-cursor.sh --reset
#
# Platform notes:
#   GPG bind mounts use .devcontainer/cursor/.host-gpg-cache/ in the repo (see README).
#   On macOS/Windows without a host agent, decrypt .env on the host for SOPS secrets.

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "ERROR: Do not source this script — run: ./scripts/start-devcontainer-cursor.sh" >&2
    return 1 2>/dev/null || exit 1
fi

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
devcontainer_path=".devcontainer/cursor/devcontainer.json"

extra_args=()
for arg in "$@"; do
    case "$arg" in
        --recreate | --reset)
            extra_args+=("$arg")
            ;;
        -h | --help)
            cat << 'EOF_HELP'
Open this repository in a Dev Container via DevPod + Cursor.

Cursor has no built-in "Reopen in Container" (unlike VS Code). DevPod builds
the devcontainer and connects Cursor over SSH — equivalent to VS Code's flow,
where load-env.sh runs inside the container after it starts (via postCreateCommand).

Usage:
  ./scripts/start-devcontainer-cursor.sh
  ./scripts/start-devcontainer-cursor.sh --recreate
  ./scripts/start-devcontainer-cursor.sh --reset

Platform notes:
  GPG bind mounts use .devcontainer/cursor/.host-gpg-cache/ in the repo (see README).
  On macOS/Windows without a host agent, decrypt .env on the host for SOPS secrets.
EOF_HELP
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

if ! command -v devpod &>/dev/null; then
    echo "ERROR: devpod not found in PATH. Install DevPod: https://devpod.sh/docs/getting-started/install" >&2
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "WARNING: Local Docker daemon is not running or not reachable. If you are using a remote DevPod provider, you can ignore this." >&2
fi

# Bind-mount sources must exist on the host (empty dirs are fine).
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh" 2>/dev/null || true

bash "${repo_root}/.devcontainer/cursor/ensure-gpg-mounts.sh"

providers_json="$(devpod provider list --output json 2>/dev/null || echo '{}')"
if [ "${providers_json}" = "{}" ]; then
    echo "ERROR: No DevPod provider installed." >&2
    echo "       Run: devpod provider add docker" >&2
    echo "       See: https://devpod.sh/docs/getting-started/quickstart" >&2
    exit 1
fi

if ! grep -q '"default"[[:space:]]*:[[:space:]]*true' <<<"${providers_json}"; then
    echo "ERROR: No default DevPod provider configured." >&2
    echo "       Run: devpod provider use docker   (or your preferred provider)" >&2
    exit 1
fi

echo "==> Starting DevPod workspace (devcontainer: ${devcontainer_path})"
if ! devpod up "${repo_root}" \
    --devcontainer-path "${devcontainer_path}" \
    --ide cursor \
    "${extra_args[@]}"; then
    echo "ERROR: devpod up failed. Common fixes:" >&2
    echo "  - devpod provider use docker" >&2
    echo "  - ensure Docker is running" >&2
    echo "  - ./scripts/start-devcontainer-cursor.sh --recreate" >&2
    exit 1
fi

echo ""
echo "==> Done. Cursor should open the workspace in the Dev Container."
echo "    One-time setup (uv sync, hooks) runs via postCreateCommand; load-env.sh loads env vars per shell."
echo "    Host ~/.gitconfig is bind-mounted read-only as ~/.gitconfig-host, copied to ~/.gitconfig;"
echo "    gh auth persists in Docker volume middleware-harvester-gh-config (run gh auth login once)."
echo "    GPG: ensure-gpg-mounts.sh prepares host cache; agent forwarding is Linux-only."
echo "    See .devcontainer/cursor/README.md for mounts and SOPS workarounds."
