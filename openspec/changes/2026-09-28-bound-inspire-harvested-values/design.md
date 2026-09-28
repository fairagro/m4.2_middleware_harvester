## Context

`IsoParser.parse_record` (`middleware/inspire/src/middleware/inspire/iso_parser.py`) is the single choke point every CSW
query strategy (CQL, XML, FES, standard) funnels through to build an `InspireRecord`. Auditing it against `main`
(2026-09-28) found no length limits on any free-text field, no count limits on any list field, no real URL-scheme check
(one loose `startswith("http")`), and codelist fields typed as free `str`.

`InspireRecord` failures already have a reporting path: `CSWClient._yield_iso_records` catches any exception from
`parse_record` and yields a `RecordProcessingError`, which the orchestrator counts as a failed record.

The first iteration of this change (PR #352, reviewed) truncated/dropped values in `IsoParser` with hardcoded limits.
Review feedback: limits must be configurable, constraints belong on the model as validation, truncation can make records
collide, and identifiers must never be placeholders. This design reflects that feedback.

## Goals / Non-Goals

**Goals:**

- Reject, rather than pass through or silently alter, harvested values that exceed configurable limits, use a disallowed
  URL scheme, or violate an ISO 19139 codelist / format.
- Keep every currently-harvested well-formed record harvestable (verified on live catalogues, see Risks).
- Derive ARC identifiers without placeholders.

**Non-Goals:** see proposal.md.

## Decisions

1. **Validation on the model, no sanitization layer.** Constraints are Pydantic annotated types on `InspireRecord` and
   its nested models (`ShortStr`, `MediumStr`, `LongStr`, `HarvestedUrl`, `LanguageCode`, `IsoDate`, codelist
   `Literal`s, `MaxItems`). A violation raises `ValidationError`; the record becomes a `RecordProcessingError` through
   the existing path. _Alternative rejected:_ truncate/drop (the first iteration) — truncating `fileIdentifier` or
   `title` can map two distinct records onto one ARC identifier; dropping silently hides broken upstream data that the
   harvest report should surface.

2. **Configurable limits via validation context.** Pydantic constraints like `Field(max_length=...)` are fixed at class
   definition, so the limits are read at validation time from `ValidationInfo.context["value_bounds"]`.
   `IsoParser(value_bounds)` calls `InspireRecord.model_validate(data, context=...)`, building nested entries as dicts
   (Pydantic only propagates context to nested models validated from dicts). With no context — direct construction in
   tests — the `ValueBounds()` defaults apply, so the model is never unbounded.

3. **Limit defaults** — three string tiers (200 / 1,000 / 10,000) and one list cap (500). A survey of 1,500 GDI-DE and
   ZALF records found maxima of 36 (identifier), 192 (title), 3,081 (abstract), 632 (contact position), 900
   (otherConstraint) and 19 (keywords): the defaults are generous multiples meant to stop pathological input, not
   right-size typical input. The list count is checked in a `BeforeValidator` so an oversized list is rejected before
   its items are validated.

4. **URL scheme allowlist is configuration; `csw_url` scheme is hardcoded.** Harvested URLs are never dereferenced by
   the harvester — they are copied into the ARC — so their allowed schemes are a security policy (`allowed_url_schemes`,
   default `http`/`https`/`ftp`; INSPIRE download links are commonly `ftp://`). `csw_url` is dereferenced by OWSLib via
   `requests`, which only speaks http(s): a functional constraint, hardcoded.

5. **Blank optional URLs mean "absent".** OWSLib reports a missing `gmx:Anchor` `xlink:href` as `""`; without treating
   blank as `None`, every live record was rejected. This normalizes absence, not a value.

6. **`dataset_uri` accepts URNs.** `gmd:dataSetURI` is a URI; URNs (`urn:sde:...`) occur on GDI-DE and are legitimate.
   Other URL fields stay URL-only.

7. **Codelists include ISO 19115-1 additions and are case-sensitive.** Catalogues moving to the newer standard must not
   be rejected; codelist values are defined in camelCase. Languages use ISO 639-2 (`^[a-z]{3}$`), which INSPIRE
   mandates; ISO 639-1 (`de`) is rejected. The e-mail check is deliberately loose (one `@`, no whitespace) — no new
   dependency, no deliverability judgement.

8. **Denominators validate as `list[int]`.** The parser passes raw values; Pydantic converts numeric strings and rejects
   the rest. (The first iteration silently dropped bad values.)

9. **Identifiers without placeholders.** `sanitize_identifier`/`to_identifier_slug` are extracted into
   `middleware.payload.identifier_sanitizer` (dependency-free; `LinkedDataMapper` keeps delegating wrappers).
   `map_investigation` sanitizes every identifier and raises `SemanticError` when the result is empty. Study/assay/
   output-URI identifiers use the title slug, else the sanitized `fileIdentifier` (unique per record), else raise.
   `"untitled"` is gone from `InspireMapper`; `regal_mapper.py` has the same pattern and is left for a follow-up.

10. **Error messages do not echo huge values.** Length/count validators report sizes and limits, not the value; Pydantic
    truncates `input_value` in its own messages. Keeps the harvest report readable under hostile input.

## Risks / Trade-offs

- **Records that harvested before may now fail.** Measured against live data (1,500 GDI-DE records across three offsets,
  plus the ZALF repository), after decisions 5 and 6: 3 new failures (0.2%), all `dataSetURI` values that are neither
  URL nor URN (`I`, `?ResourceName=`, `G:\...`) — values `main` used verbatim as the ARC output URI. Every codelist,
  language, date and e-mail value observed passed.
- **Stricter codelists could reject catalogues not yet surveyed.** The failure is loud (per-record, in the harvest
  report, with field and reason), and an operator can widen `value_bounds` limits; codelists themselves are not
  configurable, by design.
- **No live-network regression test**, matching the `csw-ssl-verify`/`csw-xml-hardening` precedents — unit tests against
  mocked `MD_Metadata`; the live survey was run manually.

## Migration Plan

Additive: `value_bounds` is optional with defaults; no YAML shape change. A config with a non-http(s) `csw_url` now
fails at startup (it could never work with OWSLib anyway).
