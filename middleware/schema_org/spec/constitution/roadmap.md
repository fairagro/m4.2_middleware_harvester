# Roadmap

## Phase 1: Foundation

- [ ] Create constitution docs (mission, tech-stack, roadmap)
- [ ] Verify schema_org plugin skeleton on `feature/schema-org-harvester`
- [ ] Define PayloadType enum entry for EDAL-PGP

## Phase 2: EDAL-PGP Mapper

- [ ] Create `spec/edal-pgp-mapping/spec.md`
- [ ] Implement `EdalPgpMapper` class
- [ ] Handle edge cases: date format, $licenseURL placeholder, duplicate authors
- [ ] Add unit tests

## Phase 3: Integration

- [ ] Register EdalPgpMapper in registry
- [ ] Test end-to-end with real EDAL-PGP dataset
- [ ] Add integration test

## Phase 4: Deployment

- [ ] Decide: harvester plugin integration vs standalone
- [ ] Configure cron schedule
- [ ] Deploy to test infrastructure

## Future RDIs (backlog)

- BonaRes
- Others as needed