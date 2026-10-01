## MODIFIED Requirements

### Requirement: Support SitemapType.mycore_solr in plugin configuration

The system SHALL support `SitemapType.mycore_solr` in linked_data plugin configuration, implemented as a shim over the
generic `mycore_solr` Protocol (adapting flat linked_data `sitemap_url` / `page_size` into Protocol type settings). The
system SHALL accept canonical `generic.protocol.mycore_solr` (`entry_url`, `page_size`) and SHALL also support
deprecated flat `protocol_type: mycore_solr` plus `sitemap_url` lifted into that nested form.

#### Scenario: Satisfies — Support SitemapType.mycore_solr in plugin configuration

- **WHEN** the conditions described by this requirement apply
- **THEN** Support `SitemapType.mycore_solr` in plugin configuration

#### Scenario: Generic protocol_type mycore_solr resolves

- **WHEN** a `generic` repository sets `protocol.mycore_solr.entry_url` or deprecated flat `protocol_type: mycore_solr`
- **THEN** the generic plugin constructs `MycoreSolrProtocol`

### Requirement: Accept a MyCoRe Solr select endpoint in entry_url; query parameters…

The system SHALL accept a MyCoRe Solr select endpoint in mycore_solr `entry_url` (deprecated alias: lifted
`sitemap_url`); query parameters are optional.

#### Scenario: Satisfies — Accept a MyCoRe Solr select endpoint in entry_url; query parameters…

- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a MyCoRe Solr select endpoint in `entry_url` (or deprecated `sitemap_url`); query parameters are
  optional

### Requirement: When entry_url has no query string (or omits overridable params),…

The system SHALL ensure that when `entry_url` has no query string (or omits overridable params), fill defaults:
`core=main`, `q=*:*`, `fl=id`, and `rows` from mycore_solr type settings `page_size`.

#### Scenario: Satisfies — When entry_url has no query string (or omits overridable params),…

- **WHEN** the conditions described by this requirement apply
- **THEN** When `entry_url` has no query string (or omits overridable params), fill defaults: `core=main`, `q=*:*`,
  `fl=id`, and `rows` from type settings `page_size`

### Requirement: Always set wt=json in software; ignore any wt already present…

The system SHALL always set `wt=json` in software; ignore any `wt` already present on `entry_url`.

#### Scenario: Satisfies — Always set wt=json in software; ignore any wt already present…

- **WHEN** the conditions described by this requirement apply
- **THEN** Always set `wt=json` in software; ignore any `wt` already present on `entry_url`

### Requirement: When entry_url already contains an overridable query parameter (q, fq,…

The system SHALL ensure that when `entry_url` already contains an overridable query parameter (`q`, `fq`, `core`, `fl`,
`rows`, …), keep the operator value.

#### Scenario: Satisfies — When entry_url already contains an overridable query parameter (q, fq,…

- **WHEN** the conditions described by this requirement apply
- **THEN** When `entry_url` already contains an overridable query parameter (`q`, `fq`, `core`, `fl`, `rows`, …), keep
  the operator-supplied value

### Requirement: Always set pagination start in software; ignore any start already…

The system SHALL always set pagination `start` in software; ignore any `start` already present on `entry_url`.

#### Scenario: Satisfies — Always set pagination start in software; ignore any start already…

- **WHEN** the conditions described by this requirement apply
- **THEN** Always set pagination `start` in software; ignore any `start` already present on `entry_url`

### Requirement: When entry_url contains a rows parameter, use it as the…

The system SHALL ensure that when `entry_url` contains a `rows` parameter, use it as the page size (it overrides type
settings `page_size`).

#### Scenario: Satisfies — When entry_url contains a rows parameter, use it as the…

- **WHEN** the conditions described by this requirement apply
- **THEN** When `entry_url` contains a `rows` parameter, use it as the page size (it overrides config `page_size`)

### Requirement: When entry_url has no rows parameter, use type page_size (default…

The system SHALL ensure that when `entry_url` has no `rows` parameter, use mycore_solr type settings `page_size`
(default 200) as Solr `rows`.

#### Scenario: Satisfies — When entry_url has no rows parameter, use type page_size (default…

- **WHEN** the conditions described by this requirement apply
- **THEN** When `entry_url` has no `rows` parameter, use type settings `page_size` (default 200) as Solr `rows`
