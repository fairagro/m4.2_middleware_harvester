# CSW Harvesting

Query the Catalogue Service for Web (CSW) endpoints and parse ISO 19139 XML into the `InspireRecord` object.

## Requirements

- [ ] Connect securely to the configured `csw_url` and retrieve all available metadata records.
- [ ] Support four mutually exclusive query modes per call:
  - **standard** — no filter; paginated fetch of all records.
  - **cql_query** — CQL text filter (e.g. `AnyText LIKE '%agriculture%'`); paginated.
  - **fes_constraints** — list of OWSLib `OgcExpression` objects; paginated.
  - **xml_query** — raw `GetRecords` XML body passed through verbatim; no pagination.
- [ ] Enforce mutual exclusion: activating more than one query mode (combining call-site arguments with Config defaults) must raise `ValueError` immediately, before any network call.
- [ ] Parse each ISO 19139 batch and yield `RecordProcessingError` for every record whose XML cannot be parsed, using the ISO identifier where available.
- [ ] If and only if a batch contains ISO records without a usable identifier (absent or `owslib_random_*`), fetch the corresponding Dublin Core batch to obtain stable identifiers for those records.
- [ ] Match DC identifiers to identifier-less ISO parse errors by associating the remaining (unmatched) DC identifiers with failed ISO records in positional order.
- [ ] Yield a `RecordProcessingError` for each unmatched DC identifier so that the harvest report can attribute errors to a specific source record.

## Edge Cases

- ISO records with a valid identifier parse fine → DC is never fetched for that batch.
- A batch is completely identifier-less (all records empty/broken) → DC batch fetched; all DC identifiers treated as failed records.
- DC batch itself fails (network error) → log warning; ISO parse errors are reported without identifiers (message includes position in batch).
- Broken XML responses or invalid attribute access → yield `RecordProcessingError`, continue iteration.
- `fes_constraints` has no Config-level equivalent because OWSLib `OgcExpression` objects are runtime-only and not YAML-serializable; it can only be supplied at call time.
- An XML query with an encoding declaration must be converted to `bytes` before being passed to OWSLib to avoid an lxml `Unicode strings with encoding declaration` error.
