# CSW Harvesting

Query the Catalogue Service for Web (CSW) endpoints and parse ISO 19139 XML into the `InspireRecord` object.

## Requirements

- [ ] Connect securely to the configured `csw_url` and retrieve all available metadata records.
- [ ] Support both standard paginated requests and raw XML request pass-through.
- [ ] Fetch stable record identifiers before loading full ISO metadata to ensure consistent pagination across CSW servers.
- [ ] Parse ISO 19139 `MD_Metadata` into a fully typed `InspireRecord`, extracting: temporal extent, spatial resolution, contacts, reference formats, spatial extents, graphic overviews, and dataset URLs.
- [ ] Yield a `RecordProcessingError` for any record whose identifier cannot be aligned or whose XML cannot be parsed.

## Edge Cases

- Some CSW servers yield random identifiers under pagination; the stable identifier obtained in the pre-fetch step must override any such value.
- Broken XML responses or invalid attribute access → yield `RecordProcessingError`, continue iteration.
