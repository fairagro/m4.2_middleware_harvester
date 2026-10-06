# Spec Delta

## ADDED Requirements

### Requirement: Authoritative PhenoRoam mapping document path

The PhenoRoam→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/phenoroam.md`](../../../../docs/mappers/phenoroam.md). This spec remains the implementation contract and
MUST NOT restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central PhenoRoam mapping doc

- **WHEN** a contributor needs PhenoRoam `phenoroam_record` source→ARC field placement rules
- **THEN** they use `docs/mappers/phenoroam.md` as the authoritative mapping source for this domain
