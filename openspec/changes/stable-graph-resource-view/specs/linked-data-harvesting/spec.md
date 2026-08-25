## MODIFIED Requirements

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a linked-data graph, the linked-data plugin MUST build a
`MappingContext` from discovery and pass it to `map_graph`. For
`UrlDiscoveryResult`, the context MUST include the discovered page URL as
`source_url` and MUST forward optional `harvest_source_id` when present so
Schema.org mapping can key `Investigation.identifier` to the harvest unit
without parsing URLs inside StableGraph. Inline discovery results without a
fetched URL MUST still pass an explicit `MappingContext()` (with null
`source_url` / `harvest_source_id`); callers MUST NOT omit the context argument.

#### Scenario: Discovery URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a page URL
- **THEN** `map_graph` MUST receive a MappingContext whose `source_url` is that
  page URL

#### Scenario: Harvest source id from sitemap is forwarded to the mapper

- **WHEN** the plugin processes a `UrlDiscoveryResult` with `harvest_source_id`
  set (e.g. MyCoRe Solr `id`)
- **THEN** `map_graph` MUST receive a MappingContext carrying that
  `harvest_source_id`

#### Scenario: Inline discovery without URL uses empty MappingContext

- **WHEN** the plugin maps a dataset from an inline discovery result with no
  landing URL
- **THEN** `map_graph` MUST be called with an explicit `MappingContext()` whose
  `source_url` and `harvest_source_id` are null, and MUST NOT invent a fake URL
  solely to populate context
