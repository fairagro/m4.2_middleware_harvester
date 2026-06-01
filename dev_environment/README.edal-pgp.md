# EDAL-PGP Harvester — Local Demo

This folder contains everything needed to run the EDAL-PGP schema.org harvester against the demo mock API or the live endpoint.

## Prerequisites

- `uv` (Python package manager)
- Docker + Docker Compose (only for the compose demo)
- Network access to `https://doi.ipk-gatersleben.de` (for the live test)

## Run 1: Compose Demo (mock API)

Builds the harvester Docker image and starts both the mock API and the harvester, using `config.edal-pgp.yaml`:

```bash
docker compose -f dev_environment/compose.edal-pgp.yaml up --build
```

The mock API writes ARC outputs to `dev_environment/demo_output/`.

## Run 2: Direct Harvester (local Python, no docker)

Requires a running Middleware API mock or real API. To start just the mock:

```bash
uv run uvicorn dev_environment.demo_api_main:app --host 0.0.0.0 --port 8000
```

Then in another terminal:

```bash
uv run python -m middleware.harvester.main -c dev_environment/config.edal-pgp.yaml
```

## Run 3: Live Pipeline Test (opt-in)

```bash
NETWORK_ENABLED=1 uv run pytest middleware/schema_org/tests/integration/test_edal_pgp_live.py -v
```

This fetches the real sitemap from `https://doi.ipk-gatersleben.de/sitemap.xml`, follows all DOI URLs, extracts JSON-LD, runs the EdalPgpMapper, and asserts at least one valid RO-Crate output.

## Operational Contract

- **Cron schedule**: Deferred to ops. The suggested cadence is **daily at 02:00 UTC**.
- **Config location** (in production): `/etc/harvester/config.yaml`
- **Binary**: `/middleware/harvester/harvester` (built by `Dockerfile.harvester`)
- **Default log level**: `INFO`
- **Harvest report**: Printed to stdout at the end of each run (JSON-LD format).
