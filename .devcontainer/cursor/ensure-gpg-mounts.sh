#!/usr/bin/env bash
# Prepare GPG bind-mount files under .devcontainer/cursor/.host-gpg-cache/
#
# Devcontainer bind mounts require sources to exist. This script refreshes stub
# files (or links a live agent socket when possible). It must never fail container
# creation — always exits 0.

set -uo pipefail

warn() {
    echo "WARN: $*" >&2
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gpg_host_dir="${1:-${script_dir}/.host-gpg-cache}"
socket_path="${gpg_host_dir}/S.gpg-agent.extra"
trustdb_path="${gpg_host_dir}/trustdb.gpg"

mkdir -p "${gpg_host_dir}" 2>/dev/null || {
    warn "cannot create ${gpg_host_dir}"
    exit 0
}

rm -f "${socket_path}" "${trustdb_path}"

socket_src=""
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -S "${XDG_RUNTIME_DIR}/gnupg/S.gpg-agent.extra" ]; then
    socket_src="${XDG_RUNTIME_DIR}/gnupg/S.gpg-agent.extra"
elif [ -S "${HOME}/.gnupg/S.gpg-agent.extra" ]; then
    socket_src="${HOME}/.gnupg/S.gpg-agent.extra"
fi

if [ -n "${socket_src}" ]; then
    if ! ln "${socket_src}" "${socket_path}" 2>/dev/null; then
        warn "cannot hard-link GPG socket (${socket_src}); agent forwarding disabled"
        touch "${socket_path}" 2>/dev/null || true
    fi
else
    touch "${socket_path}" 2>/dev/null || true
fi

if [ -f "${HOME}/.gnupg/trustdb.gpg" ]; then
    cp "${HOME}/.gnupg/trustdb.gpg" "${trustdb_path}" 2>/dev/null \
        || touch "${trustdb_path}" 2>/dev/null || true
else
    touch "${trustdb_path}" 2>/dev/null || true
fi

exit 0
