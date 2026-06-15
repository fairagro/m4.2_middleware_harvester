#!/usr/bin/env bash
# DevPod re-injects credsStore=devpod into ~/.docker/config.json on every docker call.
# Inside DinD the agent on localhost:12049 is often unreachable. Use a repo-local
# DOCKER_CONFIG without credsStore for public docker.io pulls.

setup_devcontainer_docker_config() {
    local repo_root="${1:?repo root required}"
    local docker_config_dir="${repo_root}/.docker/devcontainer"

    mkdir -p "${docker_config_dir}"
    if [ ! -f "${docker_config_dir}/config.json" ]; then
        printf '%s\n' '{"auths":{}}' > "${docker_config_dir}/config.json"
    fi
    export DOCKER_CONFIG="${docker_config_dir}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    set -euo pipefail
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    setup_devcontainer_docker_config "$(cd "${script_dir}/.." && pwd)"
    echo "✅ Using DOCKER_CONFIG=${DOCKER_CONFIG} (bypasses DevPod credsStore in ~/.docker)"
fi
