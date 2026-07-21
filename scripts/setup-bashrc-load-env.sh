#!/usr/bin/env bash
# Ensure ~/.bashrc sources load-env.sh with a clean path (no stray backslashes).

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
load_env_line="source ${script_dir}/load-env.sh"

if grep -qF 'scripts/load-env.sh' ~/.bashrc 2>/dev/null; then
    sed -i '\|scripts/load-env.sh|d' ~/.bashrc
fi

echo "${load_env_line}" >> ~/.bashrc
