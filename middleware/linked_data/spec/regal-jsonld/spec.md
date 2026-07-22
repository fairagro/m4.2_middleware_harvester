# Regal JSON-LD Harvesting

Extend the linked_data plugin with Regal (hbz) discovery, payload, and mapping
strategies so repositories such as PUBLISSO FRL can be harvested without a
separate plugin. Discovery uses the Regal `/find` JSON API; each record is
native Regal JSON-LD (not schema.org); mapping produces ARC RO-Crate JSON-LD.

## Requirements

### Discovery (`Sitemap`)

- [ ] Support a dedicated Regal sitemap type in plugin configuration.
- [ ] Accept a fully-formed Regal `/find` URL (including query parameters) in the existing `sitemap_url` config field.
- [ ] Issue HTTP GET requests to the configured `/find` URL.
- [ ] Parse the response as a JSON array of Regal JSON-LD records.
- [ ] Yield one discovery result per record that carries the record's JSON-LD payload inline (no follow-up HTML fetch).
- [ ] Use each record's `@id` as the stable discovery identity for deduplication and error reporting.
- [ ] Deduplicate discovered records by `@id` within a single harvest run.
- [ ] Paginate by advancing the `from` query parameter by the number of records returned until a page is empty or shorter than the requested page size.
- [ ] Expose `get_expected_count()` as unknown (`None`) when the `/find` response does not provide a total hit count.
- [ ] Raise `httpx.HTTPStatusError` on non-2xx HTTP responses (do not swallow).
- [ ] Raise `ValueError` when the response body is not a JSON array.

### Dataset payload

- [ ] Support a dedicated Regal dataset type in plugin configuration.
- [ ] Construct the dataset from an inline Regal JSON-LD discovery result without requiring an HTTP client.
- [ ] Parse the inline JSON-LD into an `rdflib.Graph` via rdflib's JSON-LD parser.
- [ ] Use the record `@id` (falling back to DOI when `@id` is absent) as the stable dataset identifier.
- [ ] Raise a dataset error when the discovery result type is unsupported.
- [ ] Raise a dataset error when the payload is not valid JSON-LD for rdflib.

### Mapping (`payload_type`)

- [ ] Support a dedicated Regal payload type that selects a Regal→ARC mapper.
- [ ] Map Regal `ResearchData` graphs to serialized ARC RO-Crate JSON-LD as defined in [`docs/regal_mapping.md`](../../../../docs/regal_mapping.md) and [`regal-to-arc-mapping`](../regal-to-arc-mapping/spec.md).
- [ ] Keep Regal mapping logic separate from schema.org mapping implementations (`GeneralSchemaOrgMapper`).
- [ ] Yield a mapping error (as `HarvesterError`) when the graph lacks mappable ResearchData metadata; do not crash the plugin.

## Edge Cases

- Empty JSON array on the first page → yield zero discovery results and exit cleanly.
- Record missing `@id` and DOI → skip that record without stopping discovery.
- `@id` already yielded in this run → skip as a duplicate without stopping discovery.
- Last page shorter than the requested page size → stop pagination; do not request a further empty page.
- Inline payload present but JSON-LD context unresolved / parse failure → emit a dataset or mapping error for that record and continue.
- Configured Regal dataset type receiving a URL-only discovery result → raise a descriptive dataset construction error.
- Non-`ResearchData` Regal types in the result set → skip or map-error that record according to mapper validation; do not abort the run.
