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
| `LinkedDataMapper` | `PayloadType.regal` | Map Regal vocabulary triples to ARC |

A new `DiscoveryResult` subtype carries the inline JSON object (and its stable
`@id`). This realises the existing harvesting design allowance for sitemaps that
yield raw content rather than URLs. The Regal dataset implementation accepts
`client=None` as permitted by the dataset abstraction.

Operators configure PUBLISSO-style sources with a full `/find` URL (including
`contentType:researchData` and page size via `until`), plus the three Regal
type enums — analogous to MyCoRe Solr configuration.

## Key Decisions

1. **Extend `linked_data` with Regal strategies, not a separate Regal plugin**
   — Discovery, payload parsing, and mapping are already swappable via
   registries. A second plugin would duplicate orchestration (workers, expected
   count, error yielding) while Regal fits the same Graph-centred pipeline.
   CSW-style formats remain separate plugins; Regal does not.

2. **Name strategies after the Regal platform (`regal_find` / `regal_jsonld` /
   `regal`), not `publisso`**
   — `/find`, the Regal JSON-LD context, and `regal#ResearchData` are platform
   contracts shared across Regal installations. Institution-specific filtering
   stays in the operator-supplied query URL.

3. **Inline JSON-LD in discovery results, not HTML/RDFa scraping**
   — `/find` already returns complete Regal JSON-LD records. Landing pages are
   RDFa HTML without reliable schema.org JSON-LD or content negotiation.
   Carrying the payload in discovery avoids a useless second fetch and matches
   production behaviour in `m4.2_basic_middleware`.

4. **Full `/find` URL in `sitemap_url`, no extra query-builder config**
   — Same pattern as `mycore_solr`: operators own filter and page size
   (`from` / `until`). The sitemap only paginates by advancing `from`.

5. **Regal→ARC mapper as its own `payload_type`, not reuse of `general` /
   `GeneralSchemaOrgMapper`**
   — Regal uses `https://frl.publisso.de/context.json` (DC, SKOS, BIBO,
   Bibframe, `hbz-nrw.de/regal#`), not `schema.org/Dataset`. Reusing the
   schema.org mapper would force a lossy intermediate crosswalk. Authoritative
   field rules: [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md).

6. **Keep vocabulary-specific mapper class names**
   — Plugin package and ABC are `linked_data` / `LinkedDataMapper`. Concrete
   mappers stay vocabulary-accurate (`GeneralSchemaOrgMapper`, future
   `RegalMapper`). Generic renaming must not erase that distinction.

7. **Deduplicate on Regal `@id` inside Regal discovery**
   — Base `Sitemap.discover()` currently deduplicates only `UrlDiscoveryResult`.
   Regal records are not URL discovery results, so `@id` deduplication lives in
   the Regal sitemap path (or a small shared extension for payload discovery
   results) without changing XML/MyCoRe behaviour.

8. **Do not harvest Publisso via OAI-PMH in this feature**
   — OAI-PMH (`oai_dc` / `rdf`) remains a future protocol plugin. For Regal
   sources, `/find` provides richer bulk metadata and is the path this feature
   standardises.
