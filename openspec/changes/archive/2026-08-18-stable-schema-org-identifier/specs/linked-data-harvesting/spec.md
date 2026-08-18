## ADDED Requirements

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a Schema.org graph, the linked-data plugin MUST supply the dataset's discovery identifier (the fetched page URL for HTML JSON-LD / MyCoRe Receive-URL) as mapping context so the mapper can use it as a stable identifier fallback when the graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`.

#### Scenario: Receive-URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a Receive-URL
- **THEN** `map_graph` MUST receive that page URL as source context in addition to the RDF graph
