# Spec Delta

## ADDED Requirements

### Requirement: Authoritative INSPIRE mapping document path

The INSPIRE→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/inspire.md`](../../../../docs/mappers/inspire.md). This spec remains the implementation contract and MUST
NOT restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central INSPIRE mapping doc

- **WHEN** a contributor needs INSPIRE/`InspireRecord` source→ARC field placement rules
- **THEN** they use `docs/mappers/inspire.md` as the authoritative mapping source for this domain
