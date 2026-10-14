# Spec Delta

## MODIFIED Requirements

### Requirement: Register a ckanext_dcat DataMapper

The system SHALL register a DataMapper under `MapperType.ckanext_dcat` (`mapper.type: ckanext_dcat`) accepting
`rdf_graph`, configurable with optional `mapper.catalog_name` and http(s) `mapper.catalog_url` (blank values treated as
unset). Both catalog fields are **deprecated**: catalog/RDI provenance is owned by the middleware API's `known_rdis`
registry. When either is set, configuration validation MUST succeed and MUST emit a `logger.warning` stating that the
fields are deprecated. Mapping behaviour MUST remain unchanged aside from the warning. A later breaking change MAY
remove the fields.

#### Scenario: Composes with the jsonld parser

- **WHEN** a generic repository uses nested `protocol.dcat_ap.entry_url` (or deprecated flat `protocol_type: dcat_ap` +
  `sitemap_url`), `parser.type: jsonld` and `mapper.type: ckanext_dcat`
- **THEN** config validation succeeds and each discovered dataset yields a `HarvestedArc`

#### Scenario: Catalog fields warn and still validate

- **WHEN** a `mapper:` block sets a non-blank `catalog_name` or `catalog_url`
- **THEN** configuration validation succeeds and a `logger.warning` is emitted stating that `mapper.catalog_name` /
  `mapper.catalog_url` are deprecated in favour of the API's `known_rdis`

#### Scenario: No catalog fields, no warning

- **WHEN** a `mapper:` block omits `catalog_name` / `catalog_url` or sets them blank
- **THEN** configuration validation MUST NOT emit the catalog-fields deprecation warning
