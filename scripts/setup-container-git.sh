#!/usr/bin/env bash
# Container Git setup: copy read-only host ~/.gitconfig-host to writable ~/.gitconfig
# and replace DevPod's credential.helper (port 12049) with gh.
#
# gh auth lives in ~/.config/gh (Docker volume middleware-harvester-gh-config).

set -euo pipefail

setup_container_git() {
    local host_gitconfig="${HOME}/.gitconfig-host"
    local gitconfig="${HOME}/.gitconfig"
    local host_ssh_dir="${HOME}/.host-ssh"

    if [[ -f "${host_gitconfig}" ]]; then
        cp "${host_gitconfig}" "${gitconfig}"
        chmod 600 "${gitconfig}"
        # Host config often points at DevPod's broken in-container agent.
        git config --file "${gitconfig}" --unset-all credential.helper 2>/dev/null || true
        git config --file "${gitconfig}" --add credential.helper '!gh auth git-credential'
    else
        rm -f "${gitconfig}"
        git config --file "${gitconfig}" safe.directory '*'
        git config --file "${gitconfig}" credential.helper '!gh auth git-credential'
        chmod 600 "${gitconfig}"
    fi

    unset GIT_CONFIG_GLOBAL 2>/dev/null || true

    mkdir -p "${HOME}/.config/gh"
    chmod 700 "${HOME}/.config" "${HOME}/.config/gh" 2>/dev/null || true

    if [[ -d "${host_ssh_dir}" && ! -e "${HOME}/.ssh" ]]; then
        ln -sf "${host_ssh_dir}" "${HOME}/.ssh"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_container_git
    echo "✅ Git: copied ~/.gitconfig-host → ~/.gitconfig"
    echo "   credential.helper → gh auth git-credential (DevPod helper removed)"
    if gh auth status &>/dev/null; then
        echo "✅ gh: authenticated (~/.config/gh volume)"
    else
        echo "⚠️  gh: not authenticated — run once in container: gh auth login"
    fi
    if [[ -L "${HOME}/.ssh" || -d "${HOME}/.ssh" ]]; then
        echo "✅ SSH: ~/.ssh available"
    else
        echo "ℹ️  SSH: no host ~/.ssh mount — use HTTPS + gh"
    fi
fi
