## ADDED Requirements

### Requirement: Linked-data plugin MUST detect per-run DOI collisions for Schema.org mapping

For Schema.org payload type, the linked-data plugin MUST, within each harvest run, collect all valid DOIs extracted from each mapped dataset together with its discovered `source_url` before yielding the final `HarvestedArc` for that record. A DOI MUST be treated as **colliding** when it is associated with more than one distinct `source_url` in the same harvest batch. The plugin MUST pass the colliding-DOI set into Schema.org `map_graph` mapping context so the mapper can apply RDI-specific identifier fallback.

#### Scenario: Shared DOI across two pages is flagged as colliding

- **WHEN** a harvest run processes two HTML JSON-LD datasets at `https://www.openagrar.de/receive/openagrar_mods_00088718` and `https://www.openagrar.de/receive/openagrar_mods_00109919`, and both graphs contain DOI `10.1594/PANGAEA.957630`
- **THEN** the mapper MUST receive a colliding-DOI set containing `10.1594/PANGAEA.957630` when mapping each of those records

#### Scenario: Single-page multi-DOI is not a collision

- **WHEN** a harvest run processes one dataset whose graph contains DOIs `10.3220/253-2025-54` and `10.5281/zenodo.15672440` at a single `source_url`
- **THEN** neither DOI MUST appear in the colliding-DOI set solely because multiple DOIs exist on one page

## MODIFIED Requirements

### Requirement: Linked-data plugin MUST pass the discovered dataset URL into Schema.org mapping

When mapping a Schema.org graph, the linked-data plugin MUST supply the dataset's discovery identifier (the fetched page URL) as mapping context so the mapper can use it as a stable identifier fallback when the graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`, and so the mapper can extract an RDI-specific identifier (OpenAgrar MyCoRe id) when DOI collision fallback applies.

#### Scenario: Discovery URL is available to the Schema.org mapper

- **WHEN** the plugin maps an HTML JSON-LD dataset discovered at a page URL
- **THEN** `map_graph` MUST receive that URL as `source_url` (or equivalent mapping context field)

#### Scenario: Colliding-DOI set is available to the Schema.org mapper

- **WHEN** the plugin completes DOI collision detection for a harvest batch before yielding mapped ARCs
- **THEN** each Schema.org `map_graph` call for that batch MUST receive the colliding-DOI set derived from that batch
