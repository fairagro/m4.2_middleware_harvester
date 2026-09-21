#!/usr/bin/env bash
#
# Start the local harvester against an EXTERNAL Middleware API (mTLS).
#
# Usage:
#   ./start.sh              # Start services (uses existing harvester:latest)
#   ./start.sh --build      # Bake-build harvester:latest from versions.env, then start
#

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "$script_dir"

BUILD=0
for arg in "$@"; do
  case "$arg" in
    --build | --rebuild) BUILD=1 ;;
  esac
done

echo "==> Starting INSPIRE-to-ARC Harvester..."
echo "    - Harvester will connect to the API configured in config.yaml"
echo "    - Using client certificates: client.crt, client.key"
echo ""

if [[ ! -f "client.key" ]]; then
  echo "ERROR: client.key not found. Please provide your client key."
  exit 1
fi

if [[ "$BUILD" -eq 1 ]]; then
  # Compose cannot build the Wave-C last stage alone: pins come from versions.env and
  # named contexts (export_bins / healthcheck_bins) are wired only via docker-bake.hcl.
  versions_env="${repo_root}/versions.env"
  if [[ ! -f "${versions_env}" ]]; then
    echo "ERROR: versions.env not found: ${versions_env}" >&2
    exit 1
  fi
  set -a
  # shellcheck source=/dev/null
  source "${versions_env}"
  set +a

  bake_set_args=()
  for var in PYTHON_VERSION UV_VERSION ALPINE_VERSION ALPINE_MINOR PIP_VERSION PYINSTALLER_VERSION; do
    if [[ -z "${!var:-}" ]]; then
      echo "ERROR: ${var} must be set in versions.env" >&2
      exit 1
    fi
    bake_set_args+=(--set "*.args.${var}=${!var}")
  done

  echo "==> Building harvester:latest via Bake (docker-bake.hcl)..."
  (
    cd "${repo_root}"
    docker buildx bake -f docker-bake.hcl harvester --load \
      --set "harvester.tags=harvester:latest" \
      "${bake_set_args[@]}"
  )
  echo ""
fi

# Use sops exec-env to pass the decrypted key as an environment variable
# without writing it to a physical disk file. Never pass compose --build here.
sops exec-env "${script_dir}/client.key" \
  "docker compose -f compose.yaml up"

echo ""
echo "==> Services finished!"
echo "    - View logs: docker compose -f compose.yaml logs"
echo "    - Clean up: docker compose -f compose.yaml down"
