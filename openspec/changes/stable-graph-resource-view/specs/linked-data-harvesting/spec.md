## MODIFIED Requirements

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a linked-data graph, the linked-data plugin MUST build a
`MappingContext` from discovery and pass it to `map_graph`. For
`UrlDiscoveryResult`, the context MUST include the discovered page URL as
`source_url` and MUST forward optional `harvest_source_id` when present so
Schema.org mapping can key `Investigation.identifier` to the harvest unit
without parsing URLs inside StableGraph. Inline discovery results without a
fetched URL MAY pass an empty / null MappingContext (or omit context).

#### Scenario: Discovery URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a page URL
- **THEN** `map_graph` MUST receive a MappingContext whose `source_url` is that
  page URL

#### Scenario: Harvest source id from sitemap is forwarded to the mapper

- **WHEN** the plugin processes a `UrlDiscoveryResult` with `harvest_source_id`
  set (e.g. MyCoRe Solr `id`)
- **THEN** `map_graph` MUST receive a MappingContext carrying that
  `harvest_source_id`

#### Scenario: Inline discovery without URL uses empty context

- **WHEN** the plugin maps a dataset from an inline discovery result with no
  landing URL
- **THEN** `map_graph` MAY be called with no MappingContext or with null
  `source_url` / `harvest_source_id`, and MUST NOT invent a fake URL solely to
  populate context
