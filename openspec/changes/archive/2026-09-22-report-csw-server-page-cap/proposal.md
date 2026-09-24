# Report the CSW server's advertised page-size cap

## Why

A CSW server may cap its page size below the configured `chunk_size`, and today that happens silently. Measured
2026-09-22 against `https://atlas.thuenen.de/catalogue/csw` (pycsw 3.0.dev0) for issue #19: the endpoint advertises
`MaxRecordDefault = 10` in `GetCapabilities` and enforces it as a hard ceiling, returning `numberOfRecordsReturned="10"`
for `maxRecords` of 10, 50, 100 and 151 alike.

A harvest configured with `chunk_size=500` therefore issues the same 16 requests as `chunk_size=10` and takes the same
wall-clock time, with nothing in the logs to say why. An operator tuning `chunk_size` to reduce request volume gets no
feedback that the knob is inert.

Harvest results are unaffected — `_next_start_position` paginates on the response's `nextrecord` and `returned`, never
on the requested page size, which was verified end to end (151 records, 151 distinct identifiers, 0 errors at
`chunk_size` 10, 50 and 500). This is purely an observability gap, not a correctness one.

## What Changes

- After connecting, read the `MaxRecordDefault` constraint from the cached `GetCapabilities` response and log a warning
  once when it is below the effective page size, naming both values.
- No change to paging, request construction, or record output. The configured `chunk_size` is still sent as
  `maxRecords`; we only report the discrepancy.

## Impact

- `middleware/inspire/src/middleware/inspire/capabilities.py` — **new**, readers for the `GetCapabilities` document.
  Needed because `csw_client.py` was at 999 lines against the 1000-line pylint ceiling; see design decision 4.
- `middleware/inspire/src/middleware/inspire/csw_client.py` — one call from `_connect`; the existing service-title
  extraction moves into the new module, leaving the file at 998 lines.
- `openspec/specs/csw-harvesting/` — one added requirement.
- Operators tuning `chunk_size` get a log line instead of silence. No config or API surface change.

## Out of scope

- **Connection pooling.** The measurement that produced this finding was step 1 of #19; the pooled session shim is a
  separate decision that overturns `openspec/changes/archive/2026-08-11-inspire-csw-ssl-verify/design.md:28` and is not
  proposed here.
- **Adapting `chunk_size` to the advertised cap.** Reporting only. Clamping the request to the server's cap would change
  request construction for no measured gain, and `MaxRecordDefault` is specified as a default rather than a ceiling, so
  a conforming server may well honour a larger `maxRecords` despite advertising a smaller default.
