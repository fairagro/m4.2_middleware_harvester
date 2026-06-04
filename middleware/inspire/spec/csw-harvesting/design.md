# CSW Harvesting — Design

## Key Decisions

1. **ISO-first fetch with lazy Dublin Core fallback for identifier recovery**
   — The primary path fetches only the ISO 19139 batch. ISO records with a usable identifier (not absent and not `owslib_random_*`) are processed directly without any DC request. DC is fetched only when a batch contains at least one identifier-less ISO record, because those records cannot be individually reported in the harvest error log without an identifier. The DC identifiers that do not match any successfully parsed ISO identifier are then attributed to the failed ISO records in positional order. This avoids all DC overhead for well-behaved servers while preserving error traceability on broken ones.

2. **Yield `RecordProcessingError` instead of raising from the generator**
   — OWSLib fetching can throw arbitrary network and XML parse exceptions mid-iteration. Raising would terminate the entire generator and abort the harvest run. Yielding the error lets the orchestrator log it and continue to the next record, satisfying the failure-isolation principle.

3. **Convert `MD_Metadata` to `InspireRecord` immediately after parsing**
   — OWSLib returns `MD_Metadata` with attributes typed as `str | list | ElementMap`. Mapping to `InspireRecord` (a fully typed Pydantic model) at the boundary of `CSWClient` means `mapper.py` never has to deal with OWSLib internals or ambiguous types.
