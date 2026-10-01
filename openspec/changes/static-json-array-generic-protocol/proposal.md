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
- Shared `JsonArrayProtocol` base for "JSON array of inline JSON-LD records" sources. It owns array validation,
  per-element failures and discovery-unit yielding. Subclasses supply only the page source and the record identity.
- Add `ProtocolType.regal_find` (`RegalFindProtocol`) on the same base: the protocol half of #294, ported from
  `linked_data`. The `linked_data` `regal_find` sitemap becomes a shim over it, so existing configs are unchanged.
- Dev config: PlabiPD repository entry under `generic:`.

## Capabilities

### New Capabilities

- `static-json-array-protocol`: Single-GET JSON array discovery for the generic plugin.
- `regal-find-protocol`: Shared JSON array base plus offset-paginated Regal `/find` discovery for the generic plugin.

### Modified Capabilities

- `jsonld-parser`: local resolution of Schema.org context IRIs.
- `generic-harvesting`: `harvest_source_id` is taken from inline JSON-LD discovery units.

## Non-goals

- No new `linked_data` `SitemapType` / `DatasetType`. The only `linked_data` change is the `regal_find` shim.
- The `regal_jsonld` PayloadParser port (the parser half of #294) is a separate issue.
- Schema.org context handling in the `jsonld` parser is refactored separately (#391).
- No PlabiPD-specific mapping; `schema_org_general` is reused unchanged.
