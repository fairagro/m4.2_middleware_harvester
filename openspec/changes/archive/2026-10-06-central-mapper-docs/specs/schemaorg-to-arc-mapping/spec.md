# Spec Delta

## ADDED Requirements

### Requirement: Authoritative Schema.org mapping document path

The Schema.org→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/schemaorg.md`](../../../../docs/mappers/schemaorg.md). This spec remains the implementation contract and
MUST NOT restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central Schema.org mapping doc

- **WHEN** a contributor needs Schema.org source→ARC field placement rules
- **THEN** they use `docs/mappers/schemaorg.md` as the authoritative mapping source for this domain
