# Spec Delta

## MODIFIED Requirements

### Requirement: Support SitemapType.mycore_solr in plugin configuration

The system SHALL support `SitemapType.mycore_solr` in linked_data plugin configuration, implemented as a shim over the
generic `mycore_solr` Protocol (adapting flat linked_data `sitemap_url` / `page_size` into Protocol type settings). The
system SHALL accept canonical `generic.protocol.mycore_solr` (`entry_url`, `page_size`).

#### Scenario: Satisfies — Support SitemapType.mycore_solr in plugin configuration

- **WHEN** the conditions described by this requirement apply
- **THEN** Support `SitemapType.mycore_solr` in plugin configuration

#### Scenario: Generic protocol_type mycore_solr resolves

- **WHEN** a `generic` repository sets `protocol.mycore_solr.entry_url`
- **THEN** the generic plugin constructs `MycoreSolrProtocol`

### Requirement: Accept a MyCoRe Solr select endpoint in entry_url; query parameters…

The system SHALL accept a MyCoRe Solr select endpoint in mycore_solr `entry_url`; query parameters are optional.

#### Scenario: Satisfies — Accept a MyCoRe Solr select endpoint in entry_url; query parameters…

- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a MyCoRe Solr select endpoint in `entry_url`; query parameters are optional

### Requirement: Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…

The system SHALL construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are
derived from `entry_url` (linked_data shim may supply the same URL via linked_data `sitemap_url` into Protocol
settings).

#### Scenario: Satisfies — Construct the dataset HTML page URL as {scheme}://{host}/receive/{id} where scheme…

- **WHEN** the conditions described by this requirement apply
- **THEN** Construct the dataset HTML page URL as `{scheme}://{host}/receive/{id}` where scheme and host are derived
  from `entry_url`
