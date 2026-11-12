# Proposal

## Why

INSPIRE keywords never reach ARC or Search Hub: OWSLib returns `MD_Keywords` objects, but `IsoParser` keeps only plain
strings, so `InspireRecord.keywords` is empty on real CSW data; the mapper also never emits a `Keywords` comment. Search
Hub already reads API-exported `schema:keywords` from that comment on other RDIs (basic-layout dumps). Issue #35 asked
for OntologyAnnotation/GEMET; that shape conflicts with the current Comments contract (#603 / API #578). Lock-in **A**,
extended: parser retains source name **and** optional Anchor URI / thesaurus title on the record; mapper still only
emits the transitional aggregate `Keywords` Comment. (#603 is _how_ typed keywords are written to ARC, not whether the
source URI was preserved.)

## What Changes

- `InspireRecord.keywords` becomes a list of keyword terms (`name` required; optional `url`, optional `thesaurus`
  title), still under existing value-bounds / list caps. Plain `str` inputs coerce to name-only terms for tests /
  legacy.
- `IsoParser` extracts each OWSLib `MD_Keywords` group: nested `keywords[].name`, `keywords[].url` (`gmx:Anchor`), and
  the group thesaurus title when present.
- `InspireMapper` emits Investigation Comment `Keywords` from non-empty term **names** only (comma-joined, deterministic
  trim/dedupe/sort) — same Search Hub surface as Schema.org / Regal / DCAT. URI/thesaurus are stored, not yet ARC-
  mapped.
- Update `docs/mappers/inspire.md` accordingly; correct the stale GEMET OntologyAnnotation NOTE.
- Unit tests: parser MD_Keywords with/without URL+thesaurus; mapper aggregate from names; string coercion still works.

### Non-goals

- Writing per-term `keyword […]` Comments or OntologyAnnotation keywords — that ARC shape is
  [#603](https://github.com/fairagro/m4.2_middleware_harvester/issues/603) (and related #441).
- Removing the aggregate later — [#604](https://github.com/fairagro/m4.2_middleware_harvester/issues/604) after API
  materialization.
- Inventing URIs when the CSW only supplied plain strings.
- Changing API dump export or Search Hub itself.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `csw-harvesting`: IsoParser MUST populate `InspireRecord.keywords` from OWSLib `MD_Keywords` (name + optional URL +
  optional thesaurus title) and accept plain `str` items as name-only terms.
- `inspire-to-arc-mapping`: InspireMapper MUST emit Investigation Comment `Keywords` from keyword term names when
  non-empty; authoritative doc `docs/mappers/inspire.md` MUST match. URI/thesaurus retention without ARC emission is
  allowed in this change.

## Impact

- Code: `middleware/payload/.../inspire/models.py`; `middleware/inspire/.../iso_parser.py`;
  `middleware/payload/.../inspire/mapper.py`; unit tests; `docs/mappers/inspire.md`.
- Related: Search-Hub-visible slice of #35; typed ARC keyword writing remains #603.
- Consumers: next harvest fills `schema:keywords` for BonaRes / Thünen via existing Comment materialization; URIs ready
  for a later #603-shaped mapper pass.
