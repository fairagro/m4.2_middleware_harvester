# Regal JSON-LD Harvesting — Design

## Architecture Overview

Regal support is added as three new strategies inside `middleware/linked_data`,
reusing the existing Discovery → Dataset → Graph → Mapper → ARC pipeline:

```text
RegalFindSitemap (_discover)
  └── yield JsonLdDiscoveryResult(@id, payload)
        └── RegalJsonLdDataset.from_discovery_result (no HTTP)
              └── to_graph() → rdflib.Graph
                    └── RegalMapper.map_graph() → ARC RO-Crate JSON-LD
```

| Layer | Config enum (illustrative) | Responsibility |
| ----- | -------------------------- | -------------- |
| `Sitemap` | `SitemapType.regal_find` | Paginate Regal `/find`, yield inline JSON-LD discovery results |
| `Dataset` | `DatasetType.regal_jsonld` | Parse inline Regal JSON-LD into `rdflib.Graph` |
| `LinkedDataMapper` | `PayloadType.regal_general` | Map Regal vocabulary triples to ARC |

A new `DiscoveryResult` subtype carries the inline JSON object (and its stable
`@id`). This realises the existing harvesting design allowance for sitemaps that
yield raw content rather than URLs. The Regal dataset implementation accepts
`client=None` as permitted by the dataset abstraction.

Operators configure PUBLISSO-style sources with a `/find` base URL (query-free
is fine) plus the three Regal type enums. Config `page_size` (default 200)
controls `/find` page length via `until` unless the URL supplies `until`.
Defaults fill `q=contentType:researchData`; operator query params override
overridable keys. `format=json` and pagination `from` are always set by the
software.

## Key Decisions

1. **Extend `linked_data` with Regal strategies, not a separate Regal plugin**
   — Discovery, payload parsing, and mapping are already swappable via
   registries. A second plugin would duplicate orchestration (workers, expected
   count, error yielding) while Regal fits the same Graph-centred pipeline.
   CSW-style formats remain separate plugins; Regal does not.

2. **Name strategies after the Regal platform (`regal_find` / `regal_jsonld` /
   `regal_general`), not `publisso`**
   — `/find`, the Regal JSON-LD context, and `regal#ResearchData` are platform
   contracts shared across Regal installations. The default research-data filter
   is `contentType:researchData` (overridable via URL `q`); institution-specific
   hosts differ mainly by the `/find` base URL.

3. **Inline JSON-LD in discovery results, not HTML/RDFa scraping**
   — `/find` already returns complete Regal JSON-LD records. Landing pages are
   RDFa HTML without reliable schema.org JSON-LD or content negotiation.
   Carrying the payload in discovery avoids a useless second fetch and matches
   production behaviour in `m4.2_basic_middleware`.

4. **Query-free `/find` URL with mergeable defaults (aligned with MyCoRe Solr)**
   — `sitemap_url` may be only the endpoint (e.g. `https://frl.publisso.de/find`).
   Missing overridable params are filled (`q=contentType:researchData`,
   `until` from config `page_size`). Operator-supplied query params override
   those defaults and extra keys are forwarded. Response format and pagination
   offset are not operator-configurable: `format=json` and `from` are always
   set by the software. URL `until` overrides config `page_size` (same role as
   Solr `rows`). Compact Regal `@id` values are expanded with optional
   `resource_base_url` (default: `{scheme}://{host}/resource/` from
   `sitemap_url`) so RDF subjects are absolute IRIs without hardcoding a host
   in source.

5. **Regal→ARC mapper as its own `payload_type`, not reuse of
   `schema_org_general` / `GeneralSchemaOrgMapper`**
   — Regal uses `https://frl.publisso.de/context.json` (DC, SKOS, BIBO,
   Bibframe, `hbz-nrw.de/regal#`), not `schema.org/Dataset`. Reusing the
   schema.org mapper would force a lossy intermediate crosswalk. Authoritative
   field rules: [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md).

6. **Keep vocabulary-specific mapper class names**
   — Plugin package and ABC are `linked_data` / `LinkedDataMapper`. Concrete
   mappers stay vocabulary-accurate (`GeneralSchemaOrgMapper`, future
   `RegalMapper`). Generic renaming must not erase that distinction.

7. **Deduplicate via shared `DiscoveryResult.identifier`**
   — Regal discovery fills `JsonLdDiscoveryResult.identifier` with `@id` only.
   DOI is optional publication metadata and must not be used as the discovery
   key (mixed identity schemes would break deduplication). Base
   `Sitemap.discover()` deduplicates successful results on `identifier` and
   yields `SkippedRecord`—no Regal-specific duplicate handling in the sitemap
   path.

8. **Surface unusable `/find` entries as `RecordProcessingError` (inspire-style)**
   — Missing `@id` and non-object array elements are record-level data defects.
   Yield the shared `middleware.harvester.errors.RecordProcessingError` from
   discovery (same as the inspire CSW client), not a plugin-local wrapper type.
   The linked_data plugin forwards these signals to the orchestrator so
   `failed_datasets` / `fairagro:failedRecords` stay complete
   ([`error-handling`](../../../../spec/error-handling/),
   [`harvest-report`](../../../harvester/spec/harvest-report/)).
   Duplicates remain deliberate skips (`SkippedRecord`).

9. **Do not harvest Publisso via OAI-PMH in this feature**
   — OAI-PMH (`oai_dc` / `rdf`) remains a future protocol plugin. For Regal
   sources, `/find` provides richer bulk metadata and is the path this feature
   standardises.
