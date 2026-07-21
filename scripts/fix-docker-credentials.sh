#!/usr/bin/env bash
# DinD devcontainers may inherit a host ~/.docker/config.json with credential helpers
# that are unreachable inside the container. Use a repo-local DOCKER_CONFIG for
# public docker.io pulls.

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
    echo "✅ Using DOCKER_CONFIG=${DOCKER_CONFIG} (isolated from host ~/.docker credentials)"
fi
