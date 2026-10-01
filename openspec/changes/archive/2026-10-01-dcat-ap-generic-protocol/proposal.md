# Proposal

## Why

SRADI ([m4_rdi_portfolio#8](https://github.com/fairagro/m4_rdi_portfolio/issues/8)) publishes its catalog as a
Hydra-paginated DCAT-AP JSON-LD feed (CKAN `ckanext-dcat`). The `linked_data` plugin is being phased out (#141,
#293–#296), so new sources compose the `generic` plugin from reusable parts: DCAT-AP is a **Protocol** (record
discovery), the record content is handled by a content-specific **PayloadParser** (JSON-LD) and **DataMapper**
(ckanext-dcat → ARC).

## What Changes

- Add `ProtocolType.dcat_ap` (`generic.protocol_type: dcat_ap`): follows `hydra:nextPage`, parses each catalog page
  once, and yields one inline `JsonLdDiscoveryResult` per `dcat:Dataset` (CBD plus one hop into distribution / publisher
  / contact point / spatial). `hydra:totalItems` supplies the expected count.
- Add shared inline `ParserType.jsonld` (`parser.type: jsonld`) in `middleware.parsing`: `JsonLdDiscoveryResult` →
  `ParsedPayload(rdf_graph)`, no HTTP, vocabulary-agnostic, rejects remote `@context` / `@import`.
- Add `MapperType.ckanext_dcat` (`mapper.type: ckanext_dcat`) plus optional `mapper.catalog_name` /
  `mapper.catalog_url`.
- Dev config: SRADI repository entry under `generic:`.

## Capabilities

### New Capabilities

- `dcat-ap-protocol`: Hydra-paginated DCAT-AP catalog discovery for the generic plugin.
- `jsonld-parser`: Shared inline JSON-LD PayloadParser producing `rdf_graph`.
- `ckanext-dcat-to-arc-mapping`: DCAT-AP (ckanext-dcat flavour) → ARC DataMapper.

### Modified Capabilities

None — `harvest-protocol`, `payload-parser` and `generic-harvesting` registries are extended by new keys only.

## Non-goals

- No changes to `linked_data` (no new `SitemapType` / `DatasetType`).
- Non-DCAT-AP discovery shapes (offset/limit, OGC API Records) — future `Protocol` subclasses if needed.
- Filtering non-research-data packages typed `dcat:Dataset` (see `m4.2_advanced_middleware_api#327`).
