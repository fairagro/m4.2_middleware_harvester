# CSW Harvesting

Query the Catalogue Service for Web (CSW) endpoints and parse ISO 19139 XML into the `InspireRecord` object.

## Requirements

- [ ] Support large response fetches utilizing OWSLib's internal CSW connections.
- [ ] Connect securely to `csw_url` via `CSWClient`.
- [ ] Support both raw `xml_request` parsing and standard paginated requests.
- [ ] Utilize Dublin Core schemas `getrecords2(esn="brief")` to extract stable identifiers (`_fetch_dc_ids`) before loading the full `esn="full"` ISO metadata.
- [ ] Align resulting identifiers and gracefully handle alignment faults by yielding a `RecordProcessingError`.
- [ ] Parse `MD_Metadata` outputs recursively targeting temporal, resolution, contact lists, referencing formats, and spatial extents.
- [ ] Support parsing graphic overviews and dataset URLs.

## Edge Cases

- `ows_random_*` mock IDs might be yielded by bad CSW servers; the system overrides these with the stable fetched Dublin Core ID.
- Broken XML responses or invalid attributes internally trigger `SemanticError` or `ValueError`, which are yielded as `RecordProcessingError`.
