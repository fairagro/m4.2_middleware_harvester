## ADDED Requirements

### Requirement: Support mycore_solr via generic protocol only

The system SHALL support MyCoRe Solr discovery only through nested `generic.protocol.mycore_solr` (`entry_url`,
`page_size`) with sibling `parser` / `mapper`. The system MUST NOT accept `linked_data.sitemap_type: mycore_solr` or
provide a linked_data `MycoreSolrSitemap` shim.

#### Scenario: Generic protocol_type mycore_solr resolves

- **WHEN** a `generic` repository sets `protocol.mycore_solr.entry_url`
- **THEN** the generic plugin constructs `MycoreSolrProtocol`

#### Scenario: linked_data mycore_solr is rejected

- **WHEN** a repository entry sets `linked_data.sitemap_type` to `mycore_solr`
- **THEN** configuration validation fails (the value is not a supported `SitemapType`)

## MODIFIED Requirements

### Requirement: Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…

The system SHALL construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are
derived from mycore_solr `entry_url`.

#### Scenario: Satisfies — Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…

- **WHEN** the conditions described by this requirement apply
- **THEN** Construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived
  from `entry_url`

## REMOVED Requirements

### Requirement: Support SitemapType.mycore_solr in plugin configuration

**Reason:** Hard-cut follow-up to soft-deprecation (#387 / #396). Canonical path is `generic.protocol.mycore_solr` only.

**Migration:** Convert `linked_data` + `sitemap_type: mycore_solr` to nested `generic.protocol.mycore_solr` with sibling
`parser` and `mapper` (see `docs/linked_data_to_generic.md`).

### Requirement: Deprecate linked_data SitemapType.mycore_solr with operator warning

**Reason:** Soft-deprecation window closed; warning-only path replaced by rejection.

**Migration:** Same as above; no warning is emitted — config load fails instead.
