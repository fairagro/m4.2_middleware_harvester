# Proposal

## Why

When a CSW advertises `MaxRecordDefault` below the configured page size, many servers (e.g. Thünen atlas / pycsw)
silently cap the page anyway. We still send the larger `maxRecords` and emit a WARNING — same request count, noisier
logs. Operators want the request page size clamped down and a quieter, one-shot INFO instead. This reverses the #19
“warn without clamping” product choice now that the preference is clear (#568).

## What Changes

- **BREAKING (behaviour):** When `GetCapabilities` advertises a positive `MaxRecordDefault` below the **effective** page
  size (`chunk_size`, or a valid XML `maxRecords` override), subsequent GetRecords paging uses
  `maxRecords = MaxRecordDefault` (clamp down only; never raise).
- Replace the connect-time WARNING with at most one INFO naming both numbers and that the request was clamped.
- Absent / unparsable / non-positive `MaxRecordDefault` → unchanged (configured effective page size, no clamp log).
- No config flag to restore warn-without-clamp.
- Update OpenSpec `csw-harvesting` (requirement + design decision 6) and unit tests.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `csw-harvesting`: Replace “Warn … without clamping” with clamp-down of the effective page size to advertised
  `MaxRecordDefault`, INFO once, XML override included in the effective size before clamp.

## Impact

- Code: `middleware/inspire/.../capabilities.py`, `csw_client.py` (connect + page-size resolution for
  standard/CQL/FES/`xml_query`), `tests/unit/test_capabilities.py` (+ paging coverage as needed).
- Specs: `openspec/specs/csw-harvesting/spec.md` and `design.md` decision 6.
- Non-goals: raising `chunk_size` when the advert is higher; opt-out flag; connection pooling; changing harvest-wide
  `max_records`.
- Issue: #568.
