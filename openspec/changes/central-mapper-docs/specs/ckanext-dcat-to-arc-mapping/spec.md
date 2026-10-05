# Spec Delta

## ADDED Requirements

### Requirement: Authoritative CKAN ckanext-dcat mapping document path

The CKAN `ckanext-dcat` DCAT-AP→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/ckanext-dcat.md`](../../../../docs/mappers/ckanext-dcat.md). This spec remains the implementation
contract and MUST NOT restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central ckanext-dcat mapping doc

- **WHEN** a contributor needs CKAN `ckanext-dcat` source→ARC field placement rules
- **THEN** they use `docs/mappers/ckanext-dcat.md` as the authoritative mapping source for this domain
