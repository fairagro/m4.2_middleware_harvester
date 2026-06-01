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