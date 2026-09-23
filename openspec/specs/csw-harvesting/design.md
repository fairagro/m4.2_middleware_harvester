# CSW Harvesting — Design

## Key Decisions

1. **ISO-first fetch with lazy Dublin Core fallback for identifier recovery**
   — The primary path fetches only the ISO 19139 batch. ISO records with a usable identifier (not absent and not `owslib_random_*`) are processed directly without any DC request. DC is fetched only when a batch contains at least one identifier-less ISO record, because those records cannot be individually reported in the harvest error log without an identifier. The DC identifiers that do not match any successfully parsed ISO identifier are then attributed to the failed ISO records in positional order. This avoids all DC overhead for well-behaved servers while preserving error traceability on broken ones.

2. **Yield `RecordProcessingError` instead of raising from the generator**
   — OWSLib fetching can throw arbitrary network and XML parse exceptions mid-iteration. Raising would terminate the entire generator and abort the harvest run. Yielding the error lets the orchestrator log it and continue to the next record, satisfying the failure-isolation principle.

3. **Convert `MD_Metadata` to `InspireRecord` immediately after parsing**
   — OWSLib returns `MD_Metadata` with attributes typed as `str | list | ElementMap`. Mapping to `InspireRecord` (a fully typed Pydantic model) at the boundary of `CSWClient` means `mapper.py` never has to deal with OWSLib internals or ambiguous types.

4. **CSW `startPosition` is 1-based; advance via `nextrecord` / `returned`**
   — CSW 2.0.2 positions start at 1. Starting at 0 (OWSLib's default) omits
   `startPosition` so servers begin at 1, then `start += page_size` requests
   position `page_size` again and duplicates one record per page boundary.
   Pagination therefore starts at 1 and prefers the response `nextrecord`
   (0 = done), falling back to `start + returned`, then to
   `start + batch_length` when `matches` still indicates unread records.
   Termination uses `start_position > matches` (not `>=`): position `matches`
   is still valid. If pagination does not advance past the current start,
   it stops with a warning to avoid an infinite loop on broken servers.

5. **`xml_query` reuses the same pagination loop; only paging attrs are rewritten**
   — Operators need complex FES filters that are awkward as CQL. Passing a
   full `GetRecords` document used to be a single unpaged call, so omitting
   `maxRecords` silently harvested only the server default page (often 10).
   The XML filter/query body stays intact; each page deep-copies the template
   and sets `startPosition` / `maxRecords` on that copy only. Page size defaults
   to config `chunk_size`; a valid XML `maxRecords` overrides page size only
   (same role as Solr `rows` / Regal `until` in linked_data). A valid XML
   `startPosition` overrides the initial offset. Harvest-wide caps use config
   `max_records` so operators are not forced to overload CSW `maxRecords` for
   “download only N for a test run”. Dublin Core identifier fallback for broken
   ISO batches deep-copies the template, switches `outputSchema` to CSW/DC and
   `ElementSetName` to `brief`, then applies the same paging attributes.
   Non-ISO `outputSchema` on the template is overridden to ISO 19139 on each
   ISO request copy (warned once at prepare), matching `_fetch_iso_batch`.
   GetRecords structure is validated via `_prepare_xml_query_before_network`
   in `get_records` / `get_records_async` / `get_record_count` **before**
   `connect()`, so invalid XML never triggers a CSW network call.

6. **Report the server's advertised page cap; do not clamp to it**
   — Some servers enforce the `MaxRecordDefault` capabilities constraint as a
   hard ceiling, which makes a larger `chunk_size` inert. Measured 2026-09-22
   against `atlas.thuenen.de` (pycsw 3.0.dev0, 151 records) for issue #19: it
   advertises `MaxRecordDefault = 10` and returns 10 records for `maxRecords`
   of 10, 50, 100 and 151 alike, so `chunk_size` 10, 50 and 500 all cost the
   same 16 requests. Harvest results are unaffected — decision 4's pagination
   follows `nextrecord` / `returned`, never the requested page size, verified
   at 151 records and 151 distinct identifiers for each of those `chunk_size`
   values — but the wasted configuration was previously invisible.
   `capabilities.warn_if_server_caps_page_size` therefore logs one warning at
   connect naming both numbers. We deliberately do **not** clamp the request:
   CSW 2.0.2 defines `MaxRecordDefault` as the page size used when the client
   *omits* `maxRecords`, not as a ceiling, so a conforming server may honour a
   larger value despite advertising a smaller default, and clamping would make
   paging worse against those servers to fix nothing. The readers live in
   `capabilities.py` rather than `csw_client.py` because that module sits at
   the 1000-line pylint ceiling.
