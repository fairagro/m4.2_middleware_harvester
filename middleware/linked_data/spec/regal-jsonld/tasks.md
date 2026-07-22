# Regal JSON-LD Harvesting — Tasks

- [ ] Add `SitemapType`, `DatasetType`, and `PayloadType` enum values for Regal.
- [ ] Introduce a `DiscoveryResult` subtype for inline JSON-LD payloads (stable `@id` + payload).
- [ ] Implement `RegalFindSitemap` with `/find` pagination and `@id` deduplication.
- [ ] Implement `RegalJsonLdDataset` (inline payload → `rdflib.Graph`, no HTTP required).
- [ ] Implement `RegalMapper` (`payload_type` Regal → ARC RO-Crate JSON-LD) per [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md).
- [ ] Wire registrations and ensure plugin construction works with `client=None` for Regal datasets.
- [ ] Adjust plugin error/reporting paths so non-URL discovery results expose a stable identifier.
- [ ] Add unit tests for sitemap pagination, dataset parse errors, and mapper field coverage.
- [ ] Document an example PUBLISSO/`/find` config snippet alongside existing linked_data examples (if present).
- [ ] Remove this `tasks.md` once the feature is fully implemented.
