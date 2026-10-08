## ADDED Requirements

### Requirement: Deprecate linked_data SitemapType.mycore_solr with operator warning

The system SHALL treat `linked_data` configuration with `sitemap_type: mycore_solr` as deprecated. When such a
repository config is loaded, the system MUST emit a `logger.warning` that directs operators to nested
`generic.protocol.mycore_solr` (with sibling `parser` and `mapper`). The linked_data shim MUST continue to harvest
successfully until a separate hard-cut change removes it. The system MUST NOT fail validation solely because
`sitemap_type` is `mycore_solr`.

#### Scenario: Warning on linked_data mycore_solr config load

- **WHEN** a repository entry sets `linked_data.sitemap_type` to `mycore_solr`
- **THEN** config validation succeeds and a `logger.warning` is emitted mentioning `generic.protocol.mycore_solr`

#### Scenario: Shim still harvests

- **WHEN** a repository uses deprecated `linked_data` + `sitemap_type: mycore_solr` with an otherwise valid mapper and
  HTTP settings
- **THEN** discovery still runs via the MyCoRe Solr shim and does not fail solely due to deprecation

## MODIFIED Requirements

### Requirement: Support SitemapType.mycore_solr in plugin configuration

The system SHALL support `SitemapType.mycore_solr` in linked_data plugin configuration as a **deprecated** shim over the
generic `mycore_solr` Protocol. Canonical configuration SHALL be `generic.protocol.mycore_solr` (`entry_url`,
`page_size`) with sibling `parser` / `mapper`. The system SHALL also support deprecated flat
`protocol_type: mycore_solr` plus `sitemap_url` lifted into that nested form (see generic flat-lift deprecation).

#### Scenario: Satisfies — Support SitemapType.mycore_solr in plugin configuration

- **WHEN** the conditions described by this requirement apply
- **THEN** Support `SitemapType.mycore_solr` in plugin configuration (deprecated linked_data path)

#### Scenario: Generic protocol mycore_solr is the preferred entry

- **WHEN** an operator configures MyCoRe Solr discovery
- **THEN** the preferred form is nested `generic.protocol.mycore_solr`, not `linked_data.sitemap_type: mycore_solr`
