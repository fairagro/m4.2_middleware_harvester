# EDAL-PGP Deployment — Design

## Configuration Surface

A single YAML file (`dev_environment/config.edal-pgp.yaml`) drives the EDAL-PGP plugin. It differs from the inspire demo config in two ways:

1. Uses `schema_org` plugin field instead of `inspire`.
2. Sets `payload_type: edal_pgp` to dispatch to `EdalPgpMapper`.

The config is compatible with the existing `Config` Pydantic model in `middleware/harvester/config.py`; no schema changes are needed.

### Dev config (`dev_environment/config.edal-pgp.yaml`)

```yaml
log_level: INFO

repositories:
  - rdi: "edal-pgp"
    schema_org:
      sitemap_url: "https://doi.ipk-gatersleben.de/sitemap.xml"
      sitemap_type: xml
      dataset_type: html_jsonld
      payload_type: edal_pgp
      http:
        max_requests_per_second: 0.5
        max_connections: 2
        user_agent: "FAIRagro-Middleware-Harvester/0.1 (https://github.com/fairagro)"

api_client:
  api_url: "http://middleware-api:8000"
  timeout: 60.0
  verify_ssl: false
```

The `http` settings are deliberately conservative (`0.5 req/s`, `2 concurrent`) to avoid hammering the public IPK endpoint.

## Test Strategy

| Test | Type | What it covers |
|------|------|----------------|
| `test_repository_config_with_schema_org_edal_pgp_validates` | Unit (Pydantic) | `payload_type: edal_pgp` passes mutual-exclusion validator |
| `test_repository_config_with_schema_org_returns_schema_org_config` | Unit (Pydantic) | `plugin_config` returns correct type |
| `test_schema_org_config_with_payload_type_edal_pgp_instantiates` | Unit (Pydantic) | `SchemaOrgConfig` with `PayloadType.edal_pgp` instantiates |
| `test_create_mapper_dispatches_to_edal_pgp_mapper` | Unit (Plugin) | `SchemaOrgPlugin.create_mapper()` returns `EdalPgpMapper` |
| `test_edal_pgp_live_pipeline` | Integration (opt-in) | Full pipeline against `doi.ipk-gatersleben.de`; skipped by default |

The first four tests are pure Pydantic/mock — no network. The live test uses `NETWORK_ENABLED=1`.

## Operational Contract (Cron)

Cron scheduling is **deferred to ops**. This repository ships:

1. The harvester binary (via `Dockerfile.harvester`).
2. The config file to use for EDAL-PGP.
3. A documented run command.

Ops is responsible for:

- Setting up the cron trigger (systemd timer, Kubernetes CronJob, or equivalent).
- Supplying mTLS client certificates for the production Middleware API.
- Monitoring harvest run outcomes via the JSON-LD harvest report.

Suggested schedule: **daily at 02:00 UTC** (the endpoint is a public research repository — avoid peak hours).

## Rollout Sequence

1. **Local demo**: `docker compose -f dev_environment/compose.edal-pgp.yaml up --build` — validates end-to-end against the mock API.
2. **Live pipeline test**: `NETWORK_ENABLED=1 uv run pytest middleware/schema_org/tests/integration/test_edal_pgp_live.py -v` — validates against the real endpoint.
3. **Production handover**: Send ops the binary version, config template, and cron contract.
