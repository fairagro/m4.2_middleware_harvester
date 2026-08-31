## MODIFIED Requirements

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a Schema.org graph, the linked-data plugin MUST supply the dataset's discovery identifier (the fetched page URL) as `source_url` and MUST forward optional `harvest_source_id` from `UrlDiscoveryResult` so the mapper can key `Investigation.identifier` to the harvest unit (native catalog id or sanitized page URL) without parsing URLs in the mapper.

#### Scenario: Discovery URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a page URL
- **THEN** `map_graph` MUST receive that URL as `source_url`

#### Scenario: Harvest source id from sitemap is forwarded to the mapper

- **WHEN** the plugin processes a `UrlDiscoveryResult` with `harvest_source_id` set (e.g. MyCoRe Solr `id`)
- **THEN** `map_graph` MUST receive that value as `harvest_source_id`

#### Scenario: No per-run DOI collision registry required

- **WHEN** a harvest run processes multiple Schema.org datasets including pages that share the same DOI
- **THEN** the plugin MUST NOT require a collect-then-map phase or colliding-DOI set; distinct harvest source ids or `source_url` values MUST yield distinct `Investigation.identifier` values via the mapper's harvest-source-first chain
