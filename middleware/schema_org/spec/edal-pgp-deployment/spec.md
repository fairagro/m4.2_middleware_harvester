# EDAL-PGP Deployment

Enable production-ready harvesting of the EDAL-PGP schema.org endpoint via the FAIRagro Middleware Harvester.

## Requirements

- [x] EdalPgpMapper registered in the schema_org mapper registry for `PayloadType.edal_pgp`.
- [x] Harvester `RepositoryConfig` accepts `schema_org` as a plugin field.
- [x] A local dev config (`dev_environment/config.edal-pgp.yaml`) exists for running the EDAL-PGP plugin against the demo mock API.
- [x] A compose file exists for running the EDAL-PGP harvester in Docker with the demo mock API.
- [x] Config validation tests verify that `payload_type: edal_pgp` flows through Pydantic and the plugin machinery end-to-end.
- [x] The live EDAL-PGP endpoint is reachable and the full pipeline (sitemap → HTML → JSON-LD → Graph → EdalPgpMapper → RO-Crate) produces valid output.
- [ ] Cron schedule and production deployment contract is documented for ops handover.

## Non-Goals

- Kubernetes/Helm provisioning or Helm chart restoration.
- Production mTLS certificates or sops-encrypted secrets for the EDAL-PGP source.
- Modifications to the EdalPgpMapper itself (phase 3 already complete).
- Modifications to the colleague's `feature/schema-org-harvester` branch.

## Edge Cases

| Case | Behaviour |
|------|-----------|
| Live endpoint returns 5xx | NiceHttpClient retries with exponential backoff per configured policy |
| Live endpoint returns unexpected sitemap structure | Plugin yields a `RecordProcessingError` for each unparseable dataset, logged but does not crash |
| EDAL-PGP dataset count grows | `get_expected_datasets` logs the expected count from the sitemap |
| Demo mock API goes down | Harvester exits non-zero; compose restarts via `depends_on` and `condition: service_healthy` |
| Config file missing | `Config.from_yaml_file` raises `FileNotFoundError` at startup |
