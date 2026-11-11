# Proposal

## Why

INSPIRE keywords never reach ARC or Search Hub: OWSLib returns `MD_Keywords` objects, but `IsoParser` keeps only plain
strings, so `InspireRecord.keywords` is empty on real CSW data; the mapper also never emits a `Keywords` comment. Search
Hub already reads API-exported `schema:keywords` from that comment on other RDIs (basic-layout dumps). Issue #35 asked
for OntologyAnnotation/GEMET; that shape conflicts with the current Comments contract (#603 / API #578). Lock-in **A**:
parser + transitional aggregate `Keywords` Comment only.

## What Changes

- `IsoParser` extracts keyword **names** from each OWSLib `MD_Keywords` group (`keywords[].name`) into
  `InspireRecord.keywords` (`list[str]`), with existing value-bounds / list caps unchanged.
- `InspireMapper` emits Investigation Comment `Keywords` (comma-joined, deterministic trim/dedupe/sort) when non-empty —
  same transitional Search Hub surface as Schema.org / Regal / DCAT.
- Update `docs/mappers/inspire.md` MD_Keywords row from “Not mapped” to the Comment mapping; drop or correct the stale
  GEMET OntologyAnnotation NOTE that does not match code or this MVP.
- Unit tests: parser with `MD_Keywords`-shaped input; mapper empty / present / duplicates / over-cap behaviour via
  existing bounds.

### Non-goals

- OntologyAnnotation / `OntologySourceReference` for keywords (original #35 AC) — deferred; conflicts with #603 path.
- Per-term `keyword […]` Comments, thesaurus title / Anchor URI on the model —
  [#603](https://github.com/fairagro/m4.2_middleware_harvester/issues/603) /
  [#441](https://github.com/fairagro/m4.2_middleware_harvester/issues/441).
- Removing the aggregate later — [#604](https://github.com/fairagro/m4.2_middleware_harvester/issues/604) after API
  materialization.
- Changing API dump export or Search Hub itself.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `csw-harvesting`: IsoParser MUST populate `InspireRecord.keywords` from OWSLib `MD_Keywords` keyword names (not only
  raw `str` list items).
- `inspire-to-arc-mapping`: InspireMapper MUST emit Investigation Comment `Keywords` from `record.keywords` when
  non-empty; authoritative doc `docs/mappers/inspire.md` MUST match.

## Impact

- Code: `middleware/inspire/.../iso_parser.py`; `middleware/payload/.../inspire/mapper.py`; unit tests under
  `middleware/inspire/tests` and `middleware/payload` inspire mapper tests; `docs/mappers/inspire.md`.
- Model: keep `keywords: list[str]` — no new nested keyword type in this change.
- Related tracking: closes the Search-Hub-visible slice of #35; OntologyAnnotation / per-term remain on #603/#441.
- Consumers: next harvest fills `schema:keywords` for BonaRes / Thünen once API materializes the Comment (existing
  path).
