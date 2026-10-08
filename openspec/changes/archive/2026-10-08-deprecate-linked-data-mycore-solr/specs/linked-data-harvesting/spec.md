## ADDED Requirements

### Requirement: Deprecate sitemap_type mycore_solr under linked_data

The system SHALL deprecate `linked_data.sitemap_type: mycore_solr`. Config load for such a repository MUST emit a
`logger.warning` directing operators to `generic.protocol.mycore_solr` with sibling `parser` and `mapper`. Other
`sitemap_type` values are unaffected. Harvest behaviour for the deprecated path MUST remain unchanged aside from the
warning.

#### Scenario: mycore_solr linked_data path warns

- **WHEN** a linked_data repository sets `sitemap_type: mycore_solr`
- **THEN** a deprecation `logger.warning` is emitted and validation does not fail for that reason alone

#### Scenario: Other sitemap types do not warn for this reason

- **WHEN** a linked_data repository sets `sitemap_type` to `xml` or `regal_find`
- **THEN** the mycore_solr deprecation warning is not emitted for that repository
