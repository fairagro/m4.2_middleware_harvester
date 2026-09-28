## Context

`IsoParser.parse_record` (`middleware/inspire/src/middleware/inspire/iso_parser.py`) is the single choke point every CSW
query strategy (CQL, XML, FES, standard) funnels through to build an `InspireRecord`. Auditing it against `main`
(2026-09-28) found:

- Free text with no length cap: `title`, `abstract`, `lineage`, `supplemental_information`, `purpose`, `edition`,
  `alternate_title`, `status`, every string inside `keywords` / `constraints` / `access_constraints` / `use_constraints`
  / `classification` / `other_constraints`, `Contact.name`/`organization`.
- List fields with no count cap: `keywords`, `topic_categories`, `contacts`, `constraints`, `resource_identifiers`,
  `resource_language`, `graphic_overviews`, `dates`, `spatial_resolution_denominators`, `spatial_resolution_distances`,
  `creators`, `publishers`, `contributors`, `access_constraints`, `use_constraints`, `classification`,
  `other_constraints`, `other_constraints_url`, `distribution_formats`, `online_resources`, `conformance_results`,
  `reference_systems`.
- URL fields with no real scheme check: `dataset_uri`, `graphic_overviews`, `other_constraints_url`, `lineage_url`,
  `ResourceIdentifier.url` (a loose `code.startswith("http")`), `DistributionFormat.*_url`, `OnlineResource.url` (the
  actual download link — only a truthiness check), `ConformanceResult .specification_title_url`,
  `ReferenceSystem.*_url`.
- `_extract_resolution_denominators`'s `int(d) for d in denoms if d` — unguarded, unlike its neighbor
  `_extract_resolution_distances`'s already-guarded `float(dist)`.

`middleware/inspire/src/middleware/inspire/csw_client.py` is exactly 1000 lines against pylint's `max-module-lines=1000`
ceiling (confirmed via `wc -l` and a clean `pylint` 10.00/10 at exactly that count) — but this change does not touch
`csw_client.py` at all; all bounding lives in `iso_parser.py` (475 lines, ample headroom) and the new `value_bounds.py`
module.

Separately, `middleware/payload/src/middleware/payload/linked_data_mapper /linked_data_mapper.py` already has
`LinkedDataMapper.sanitize_identifier`/ `.to_identifier_slug` (character-allowlist + 80-char slug).
`middleware/inspire /src/middleware/inspire/mapper.py` has its own private `_to_identifier_slug` — functionally
near-identical but with no character-allowlisting, and `map_investigation` only invokes it for identifiers that already
"look like a URL".

## Goals / Non-Goals

**Goals:**

- Bound every unbounded string/list/URL field reachable from harvested CSW/ISO-19139 data, without making any
  currently-successful parse fail.
- Fix the `int()` guard so one malformed denominator drops that value, not the record.
- Stop `InspireMapper` from duplicating `middleware.payload`'s identifier sanitization, and close the gap where a raw
  (non-URL) `fileIdentifier` was never sanitized at all.
- Add cheap, low-risk config-level bounds (`csw_url` scheme, `max_records` ceiling).

**Non-Goals:** see proposal.md.

## Decisions

1. **New `value_bounds.py`, not inline in `iso_parser.py`** — `iso_parser.py` has room (475/1000 lines), so this isn't
   the pylint-line-budget workaround `xml_hardening.py`/ `http_pooling.py` were. The reason here is testability: the
   helpers are pure functions (`str`, `urllib.parse` only, no OWSLib), so `test_value_bounds.py` can assert
   truncation/URL-scheme logic directly with no `MD_Metadata` mock machinery — the same reasoning that already makes
   `middleware.payload.person_contacts`/ `person_names` standalone modules `mapper.py` imports as plain functions,
   rather than inlining that logic into the mapper.

2. **Three string-length tiers (200 / 1,000 / 10,000 chars), one shared list cap (500 items)** — `MAX_STR_SHORT` for
   code-like fields (edition, status, language codes, units); `MAX_STR_MEDIUM` for title-length free text, identifiers,
   list-element strings, and every URL field's own length; `MAX_STR_LONG` for paragraph-length free text (abstract,
   lineage, supplemental_information, `OnlineResource.description`). These are generous multiples over real ISO 19139
   content (real titles run well under a few hundred chars; abstracts are realistically a few KB) — the goal is bounding
   pathological input, not right-sizing typical input. One shared `MAX_LIST_ITEMS=500` rather than per-field tuning:
   every one of these list fields has single-digit-to-low- tens cardinality in real records, so 500 is already a large
   multiplier while keeping the constant surface small.

3. **Drop-or-truncate, never record-fatal** — Every new bound either truncates a string or drops a bad list element/URL,
   matching the _existing_ convention already in this file (`_extract_identification_list`'s `isinstance(i, str)` check
   silently omits non-string elements today). `SemanticError` stays reserved for the three pre-existing
   whole-record-fatal cases (missing identifier/title/abstract) — none of which change. `OnlineResource.url` is the one
   exception requiring care: it is non-optional (`models.py: url: str`), so an invalid URL there means the whole
   `OnlineResource` entry is skipped (not appended), rather than trying to construct the model with an invalid required
   field.

4. **`valid_http_url` allowlists `http`/`https` only, via `urllib.parse.urlsplit`, and rejects protocol-relative URLs**
   — `javascript:`, `file:`, `data:`, `ftp:` all yield a scheme outside the allowlist; `//host/path` yields an empty
   scheme, also rejected (this harvester never dereferences a URL relative to "current protocol", so requiring an
   explicit scheme is a security boundary, not a data-quality call). `verify`/`cert`/ `auth` continue to flow through
   per-request from OWSLib exactly as before — pooling and validation both operate independently of TLS behaviour
   (`openspec/specs/csw-ssl-verify/`).

5. **The `int()` guard uses `contextlib.suppress(ValueError, TypeError)`** — identical to the pattern already three
   lines below it in `_extract_resolution_distances`. No magnitude clamp: `sys.get_int_max_str_digits()` (Python 3.12
   default 4300) already bounds `int()`-from-string CPU cost; judging what denominator value is a "plausible" map scale
   is semantic validation, explicitly out of scope (see proposal.md Non-Goals).

6. **Loop iteration is capped at the source (`items[:MAX_LIST_ITEMS]`), not only the output list** — for fields built
   via `for i in range(max_len)` zipping (resource identifiers, conformance results) or direct iteration (contacts,
   dates, distances), the cap is applied to the _input_ slice before the loop runs, not via a wrapping `bounded_list()`
   call after building the full list. This bounds the CPU/memory cost of construction itself, not just the final size —
   relevant because a hostile server controls the _pre-cap_ list length directly.

7. **Extract `sanitize_identifier`/`to_identifier_slug` into a new, dependency-free
   `middleware.payload.identifier_sanitizer` module; `LinkedDataMapper` keeps them as delegating wrappers** —
   `InspireMapper` already imports two other standalone payload helpers this way
   (`person_contacts.require_nonempty_person_given_names`, `person_names.split_display_name`); this is the same pattern
   applied to identifier sanitization. _Alternative considered:_ have `mapper.py` call
   `LinkedDataMapper.sanitize_identifier`/`.to_identifier_slug` directly (both are plain static/classmethods, so this is
   legal without subclassing) — rejected because it pulls in `LinkedDataMapper`'s full import chain (`DataMapper`,
   `rdflib.Graph`, `StableGraph`, `MapperConfig`) for two string functions, and couples INSPIRE to an unrelated class's
   future changes. The extraction is a plain-function import, **not** a class-hierarchy change — `InspireMapper` still
   does not subclass anything from `middleware.payload`, unchanged from today's architecture.

8. **`to_identifier_slug` returns `None` on empty input (unlike the old private `_to_identifier_slug`, which returned
   `"untitled"`)** — the shared function's contract already matches its other three callers (`regal_mapper.py`,
   `general_schema_org_mapper.py`), which all supply their own `or "untitled"`/ `or "fallback"` at the call site.
   `mapper.py`'s four call sites now do the same, preserving today's exact fallback behavior (verified with a dedicated
   parity test).

9. **`map_investigation` now sanitizes every identifier, not only URL-shaped ones** — after the existing URL-shaped
   branch (unchanged), the identifier — URL-slugified or raw — is unconditionally passed through `sanitize_identifier`.
   This is idempotent on an already-slugified value (its character set is already a subset of `sanitize_identifier`'s
   allowlist), so the URL-shaped path is unaffected in practice; the raw `fileIdentifier` path gains the same
   character-allowlisting it never had.

10. **`csw_url` scheme validation raises; harvested-data URL validation drops** — a bad `csw_url` is fatal
    misconfiguration (fails at `Config` construction, before any harvest starts), consistent with the existing
    `user_agent_must_be_single_line` validator in the same file. A bad URL _inside a harvested record_ is exactly the
    kind of per-record defensive case this whole change treats as drop-not-fail.

11. **`max_records` gains `ge=1, le=1_000_000`, `None` untouched** — Pydantic applies `ge`/`le` only to the non-`None`
    branch of `int | None`, so the documented "harvest everything" default is unaffected (verified with a regression
    test). The ceiling exists to catch an operator typo (e.g. an extra zero), not to constrain a real full-catalogue
    harvest — national INSPIRE catalogues top out in the low hundreds of thousands of records. `ge=1` additionally
    rejects `max_records=0`, a likely-typo value that would silently harvest nothing.

## Risks / Trade-offs

- **Truncation could theoretically cut a legitimately very long abstract.** Accepted: `MAX_STR_LONG=10,000` chars is
  generous, and a truncated-but-present abstract is strictly better than the status quo (fully unbounded, in-memory,
  per-record).
- **Two additive config constraints could reject a previously-accepted config.** An operator with `csw_url: ftp://...`
  (unlikely — CSW is HTTP-only by protocol) or `max_records` set above 1,000,000 would now fail at startup instead of
  misbehaving silently later. Both are startup-time, loud failures, not silent data loss.
- **No live-network regression test**, matching the `csw-ssl-verify`/`csw-xml-hardening`/ `csw-http-pooling` precedents
  — coverage is unit-level, asserting the mechanism (truncation, drop, guard) against mocked `MD_Metadata` objects.

## Migration Plan

Additive: no new config field, no YAML shape change. Existing valid configs (http(s) `csw_url`, `max_records` unset or ≤
1,000,000) are entirely unaffected. An existing config with a non-http(s) `csw_url` or an out-of-range `max_records`
would now fail `Config` validation at startup — this is a correction of a previously-silent gap, not a behavior change
any legitimate deployment should be relying on.
