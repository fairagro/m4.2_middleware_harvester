# Roadmap

## Phase 1: Foundation

- [x] Create constitution docs (mission, tech-stack, roadmap)
- [x] Verify schema_org plugin skeleton on `feature/schema-org-harvester`
- [x] Define PayloadType enum entry for EDAL-PGP

## Phase 2: EDAL-PGP Mapper

- [x] Create `spec/edal-pgp-mapping/spec.md`
- [x] Implement `EdalPgpMapper` class
- [x] Handle edge cases: date format, $licenseURL placeholder, duplicate authors
- [x] Add unit tests

## Phase 3: Integration

- [x] Register EdalPgpMapper in registry (`@SchemaOrgMapper.register(PayloadType.edal_pgp)`)
- [x] Record-fixture integration test (real plugin pipeline with mocked HTTP, 2 datasets)
- [x] Live opt-in integration test (skipped by default, set `NETWORK_ENABLED=1`)

## Phase 4: Deployment

- [x] Harvester plugin integration confirmed — EdalPgpMapper registered, `payload_type: edal_pgp` in config
- [x] Dev config and compose file created (`dev_environment/config.edal-pgp.yaml`, `compose.edal-pgp.yaml`)
- [x] Config validation tests (4 new) verify full Pydantic + plugin machinery
- [x] Spec + design docs for deployment (`middleware/schema_org/spec/edal-pgp-deployment/`)
- [x] Live pipeline verified against `doi.ipk-gatersleben.de` — produces valid RO-Crate output
- [ ] Cron schedule: deferred to ops (see `dev_environment/README.edal-pgp.md` for contract)
- [ ] Deploy to test infrastructure: deferred to ops

## Future RDIs (backlog)

- BonaRes
- Others as needed