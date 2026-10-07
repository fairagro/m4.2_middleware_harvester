# Spec Delta

## ADDED Requirements

### Requirement: Authoritative Regal mapping document path

The Regal→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/regal.md`](../../../../docs/mappers/regal.md). This spec remains the implementation contract and MUST NOT
restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central Regal mapping doc

- **WHEN** a contributor needs Regal source→ARC field placement rules
- **THEN** they use `docs/mappers/regal.md` as the authoritative mapping source for this domain
