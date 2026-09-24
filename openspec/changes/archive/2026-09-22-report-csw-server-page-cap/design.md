# Design — Report the CSW server's advertised page-size cap

## Context

Measured for issue #19 against `https://atlas.thuenen.de/catalogue/csw` (pycsw 3.0.dev0, 151 records). `GetCapabilities`
advertises:

```xml
<ows:Constraint name="MaxRecordDefault">
  <ows:Value>10</ows:Value>
</ows:Constraint>
```

and the server enforces it as a ceiling. OWSLib already parses this into `CatalogueServiceWeb.constraints`, a
`dict[str, Constraint]` whose entries expose `.values` as a list of strings — so the information is available with no
extra request.

## Decisions

### 1. Warn, do not clamp

We keep sending the configured `chunk_size` as `maxRecords` and only report the mismatch.

`MaxRecordDefault` is specified in CSW 2.0.2 as the page size a server uses when the client omits `maxRecords` — it is
_not_ defined as a ceiling. This deployment enforces it as one, but a conforming server may honour a larger `maxRecords`
while still advertising a smaller default. Clamping our request to the advertised value would therefore make paging
_worse_ against conforming servers, to fix nothing: paging already follows the server's `nextrecord` / `returned`, so an
over-large request costs us nothing beyond an unmet expectation.

### 2. Warn once, at connect, not per page

The constraint comes from `GetCapabilities`, which is fetched once per `CatalogueServiceWeb`. Logging from `_connect`
gives one line per client lifecycle. Logging per page would emit one warning per request for the entire harvest —
thousands of identical lines on a large endpoint.

Consequence: `get_expected_datasets` and `run` open separate `CSWClient` contexts (`plugin.py:31,72`), so a full harvest
logs this twice. Accepted; two lines is not noise worth plumbing shared state for, and that duplication is tracked on
its own in #19.

### 3. Compare against the configured `chunk_size`, tolerate a missing or unparsable constraint

`_connect` does not know the effective page size for an `xml_query` harvest — an XML `maxRecords` attribute can override
`chunk_size`, and that is resolved later in `_prepare_xml_paging`. Comparing against `self._config.chunk_size` at
connect time is the honest approximation and covers the CQL, FES and standard modes exactly.

For `xml_query` the comparison may be against the wrong number. That is acceptable: the warning names both values it
compared, so the message stays truthful even when the effective page size differs. A precise check would mean deferring
the warning into the paging loop, which decision 2 rejects.

Servers that advertise no `MaxRecordDefault`, or a non-numeric value, are common enough that neither may raise. Reuse
the existing `_coerce_result_int` helper, which already returns `None` on junk, and say nothing when the value is absent
or unparsable.

### 4. A new `capabilities.py` module, not more lines in `csw_client.py`

`csw_client.py` was at 999 lines against the 1000-line `max-module-lines` pylint ceiling, so this change could not be
added to it at all — an import plus a call is two lines.

Extracting a `capabilities.py` module for readers of the `GetCapabilities` document is the honest fix and a coherent
grouping. It takes the existing service-title extraction with it, which turns four lines of `_connect` into two and
leaves `csw_client.py` at 998. Same move as `xml_hardening.py` in the #16 change, for the same reason.

**That the ceiling forced this is worth noting on its own.** `csw_client.py` sits one line under a hard lint limit, so
the next person to touch it hits the same wall. Splitting it properly — the ISO parsing, the paging loop and the retry
machinery are three separable concerns — is out of scope here but should be its own issue.

### 5. Duplicate the int coercion rather than import it

The natural reuse is `CSWClient._coerce_result_int`, which already tolerates this exact shape (strings, and lists by
recursing into the first element). It cannot be imported: `csw_client` imports `capabilities`, so reaching back would be
a cycle.

`capabilities.py` therefore carries its own `_first_int`. It is a near-duplicate, deliberately — the alternative is
moving `_coerce_result_int` out of `CSWClient`, which touches its five other call sites (`nextrecord`, `returned`,
`matches`, XML `maxRecords`, XML `startPosition`) for no benefit to this change. `_first_int` additionally rejects
non-positive values, which the caller wants and `_coerce_result_int` deliberately does not do.

## Risks

- **`Constraint.values` shape.** Depends on OWSLib's capabilities parsing. Guarded: we index defensively and coerce, so
  a shape change degrades to no warning rather than an exception during connect. A connect-time crash here would break
  harvesting, so the guard matters more than the warning does.
- **Log volume.** One line per client lifecycle, emitted only on mismatch. Negligible.
