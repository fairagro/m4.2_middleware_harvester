# Proposal

## Why

PlabiPD ([m4_rdi_portfolio#7](https://github.com/fairagro/m4_rdi_portfolio/issues/7)) publishes its published-genome
catalog as a single static JSON file: an array of Schema.org `Dataset` records
([usadellab/pubplant2schemaorg](https://github.com/usadellab/pubplant2schemaorg) `genomes.json`). The `linked_data`
plugin is being phased out (#141, #293–#296), so the source is composed from `generic` plugin parts: a **Protocol** that
splits the array into records, the shared `jsonld` **PayloadParser**, and the existing `schema_org_general`
**DataMapper**.

## What Changes

- Add `ProtocolType.static_json_array` (`generic.protocol_type: static_json_array`): one GET of `generic.sitemap_url`,
  one inline `JsonLdDiscoveryResult` per array element, with a content-hash composite identifier (several records share
  a DOI in `genomes.json`) that is also supplied as `harvest_source_id`. The array length supplies the expected count.
- `JsonLdDiscoveryResult` gains an optional `harvest_source_id`. `GenericPlugin` passes it into
  `MappingContext.harvest_source_id`.
- `jsonld` parser: a top-level Schema.org context IRI (`http(s)://schema.org[/]`) is replaced by the local
  `{"@vocab": "http://schema.org/"}` instead of being rejected or fetched. All other remote contexts are still rejected.
- Dev config: PlabiPD repository entry under `generic:`.

## Capabilities

### New Capabilities

- `static-json-array-protocol`: Single-GET JSON array discovery for the generic plugin.

### Modified Capabilities

- `jsonld-parser`: local resolution of Schema.org context IRIs.
- `generic-harvesting`: `harvest_source_id` is taken from inline JSON-LD discovery units.

## Non-goals

- No changes to `linked_data` (no new `SitemapType` / `DatasetType`).
- No PlabiPD-specific mapping; `schema_org_general` is reused unchanged.
