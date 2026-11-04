# Linked Data Harvesting

## Purpose

Historical capability name for sources that formerly used the `linked_data:` repository plugin key. That key is removed;
equivalent harvest uses `generic` with nested `protocol` and sibling `parser` / `mapper`. Concrete discovery, parse, and
map behaviour lives under `generic-harvesting` and the feature-split specs below. Operator migration:
`docs/linked_data_to_generic.md`.

## Requirements

### Requirement: Reject the linked_data plugin key

The system SHALL NOT provide a harvestable `linked_data` repository plugin key. Sources formerly configured under
`linked_data` MUST use `generic` with nested `protocol` and sibling `parser` / `mapper`. Concrete discovery, parse, and
map behaviour for those sources is specified under `generic-harvesting` and the relevant protocol/parser/mapper specs
(e.g. xml sitemap, MyCoRe Solr, Regal, html_jsonld).

#### Scenario: linked_data plugin key is not available

- **WHEN** an operator configures a repository with plugin key `linked_data`
- **THEN** configuration validation fails at startup
- **AND** no LinkedDataPlugin harvest path runs

#### Scenario: Equivalent harvest uses generic

- **WHEN** a repository that previously used linked_data xml sitemap + html_jsonld is configured as `generic` with the
  corresponding nested `protocol`, sibling `parser`, and `mapper`
- **THEN** harvest yields remain observationally equivalent for successful records (same PayloadKind path into the
  shared DataMapper)

## Feature split

- `openspec/specs/xml-sitemap-parser/spec.md` — XML sitemap discovery from a single sitemap URL and dataset URL
  extraction.
- `openspec/specs/sitemap-mycore-solr/spec.md` — MyCoRe Solr JSON discovery source; Solr pagination and `/receive/{id}`
  URL construction.
- `openspec/specs/linked-data-dataset-abstraction/spec.md` — Dataset payload abstraction and provider-specific dataset
  wrappers.
- `openspec/specs/html-jsonld-dataset/spec.md` — Dataset implementation that fetches an HTML page and extracts embedded
  JSON-LD.
- `openspec/specs/regal-jsonld/spec.md` — Regal `/find` discovery, inline Regal JSON-LD datasets, and Regal→ARC mapping.
- `openspec/specs/regal-to-arc-mapping/spec.md` — Regal ResearchData graph → ARC implementation contract (authoritative
  field rules in `docs/mappers/regal.md`).
- `openspec/specs/linked-data-mapper/spec.md` — Graph-to-ARC mapping and RO-Crate serialization.
