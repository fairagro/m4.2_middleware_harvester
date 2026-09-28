## Why

Harvested INSPIRE CSW/ISO-19139 values reach an ARC with type-guards but essentially no bounds.
`openspec/principles.md`'s "Security by default" rule treats endpoint input as untrusted; today it is not treated that
way in practice:

- **No length caps anywhere.** `title`, `abstract`, `lineage`, every constraint string, every
  `Contact.name`/`organization` — a hostile or misconfigured CSW server can return arbitrarily large strings for any of
  these, all the way into an ARC.
- **No list-count caps anywhere.** `keywords`, `contacts`, `resource_identifiers`, `conformance_results` and a dozen
  other list fields on `InspireRecord` are built with loop bounds directly controlled by the server's response
  (`middleware/inspire/src/middleware/inspire/iso_parser.py`, e.g.
  `max_len = max(len(uricode_list), len(uricodespace_list))`).
- **No real URL-scheme validation.** The only check anywhere is a loose `code.startswith("http")` on one field
  (`ResourceIdentifier.url`); every other URL field — including `OnlineResource.url`, the literal
  download-link/service-endpoint URL — is passed straight through with no scheme check at all. `javascript:`, `file:`,
  `data:` URIs are all currently accepted verbatim.
- **An unguarded `int()` fails a whole record, not just one bad value.** `_extract_resolution_denominators`
  (`iso_parser.py`) does `int(d) for d in denoms if d` with no exception guard. A single non-numeric denominator in an
  otherwise-valid record raises `ValueError`, caught only by `csw_client.py`'s generic
  `except Exception → RecordProcessingError`, discarding the entire record.
- **INSPIRE duplicates rather than reuses existing sanitization.** `middleware.payload` already has a safer
  `sanitize_identifier`/`to_identifier_slug` pair (`LinkedDataMapper`), but `InspireMapper` carries its own private,
  less-safe reimplementation, and never sanitizes a raw (non-URL-shaped) `fileIdentifier` at all.

Tracked as [#20](https://github.com/fairagro/m4.2_middleware_harvester/issues/20). The issue explicitly left open
whether this should be (a) defensive limits or (b) semantic validation of data quality; **this change is (a) only**,
confirmed by the project owner. Semantic validation (malformed dates, out-of-range bboxes, non-resolvable URLs) is a
separate, open-ended concern overlapping issue #132.

## What Changes

- New `middleware/inspire/src/middleware/inspire/value_bounds.py`: `truncate`/ `bounded_str` (string length caps, three
  tiers: 200/1,000/10,000 chars), `bounded_list` (500-item cap), `valid_http_url` (http(s)-only, length-bounded,
  drop-not-raise).
- `iso_parser.py`: every unbounded string/list/URL extraction site now bounded (see design.md for the full site-by-site
  inventory). All bounding is **drop-or-truncate, never record-fatal** — consistent with the file's existing convention
  of silently omitting malformed list elements.
- The `_extract_resolution_denominators` `int()` coercion is now guarded with
  `contextlib.suppress(ValueError, TypeError)`, matching the identical pattern already used two methods below it for
  distance coercion. **Behavior fix**: a malformed denominator no longer fails the whole record.
- New `middleware/payload/src/middleware/payload/identifier_sanitizer.py`: extracted
  `sanitize_identifier`/`to_identifier_slug` as plain functions.
  `LinkedDataMapper.sanitize_identifier`/`.to_identifier_slug` become thin delegating wrappers (existing callers/tests
  unaffected). `middleware.inspire.mapper.InspireMapper` now imports and uses these directly instead of its private
  duplicate, and its `map_investigation` now allowlist-sanitizes every identifier, not only URL-shaped ones.
- `Config.csw_url` gains an http(s)-only scheme validator (raises on invalid config). `Config.max_records` gains
  `ge=1, le=1_000_000` (the documented `None` = "harvest everything" default is untouched — Pydantic only applies bounds
  to the non-`None` branch).

## Non-Goals

- **Semantic/data-quality validation** — malformed dates, out-of-range bounding boxes, unreachable URLs, or junk
  constraint text are not flagged or rejected here. That is issue #20 option (b), overlapping #132, and is explicitly
  out of scope for this change.
- **Response-body-size limiting.** Would touch `http_pooling.py`/OWSLib's HTTP transport layer, not value bounding — #19
  (`openspec/changes/2026-09-28-pool-csw-http-sessions/`) just shipped in that exact module. Kept as a separate,
  independently reviewable follow-up.
- **Scale-denominator magnitude plausibility.** Python 3.12's `sys.get_int_max_str_digits()` already bounds the CPU cost
  of `int()`-from-string; a further "is this a sane map scale" clamp is a semantic judgment, deliberately punted rather
  than silently decided either way.
- **INSPIRE routing through `middleware.payload`'s `DataMapper` pipeline.** `InspireMapper` reuses two plain
  sanitization _functions_; it is not becoming a `DataMapper`/ `LinkedDataMapper` subclass. Mapper-class-hierarchy
  coupling between INSPIRE and `middleware.payload` remains out of scope, unchanged from today's architecture.

## Capabilities

### New Capabilities

- `inspire-value-bounds`: Defensive length/count/URL-scheme bounds for harvested INSPIRE CSW/ISO-19139 values, plus
  config-level bounds on `csw_url`/`max_records`.

### Modified Capabilities

- (none)

## Impact

- **Affected domains**: new `openspec/specs/inspire-value-bounds/`; adjacent to `csw-harvesting` (the fields being
  bounded) and `csw-ssl-verify` (the `middleware.inspire.config` field-validator pattern this follows).
- **Code**: new `middleware/inspire/src/middleware/inspire/value_bounds.py`; new
  `middleware/payload/src/middleware/payload/identifier_sanitizer.py`;
  `middleware/inspire/src/middleware/inspire/{iso_parser.py,mapper.py,config.py}`;
  `middleware/payload/src/middleware/payload/linked_data_mapper/linked_data_mapper.py`; new unit tests under
  `middleware/inspire/tests/unit/` and `middleware/payload/tests/unit/`.
- **Config**: two new validation constraints (`csw_url` scheme, `max_records` ceiling). Both are additive checks on
  existing fields — no new field, no YAML shape change. A previously-accepted config with a non-http(s) `csw_url` or
  `max_records > 1_000_000` would now be rejected at startup (see design.md Migration Plan).
- **Dependencies**: none new.
- **Behaviour**: harvested values are truncated/dropped rather than passed through unbounded; one behavior fix (a
  malformed resolution denominator no longer fails the whole record). No change to TLS/auth/retry semantics.
