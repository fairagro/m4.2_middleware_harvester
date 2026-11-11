# Design

## Context

See proposal.md — Why. Today `_extract_identification_list("keywords", …)` keeps only `isinstance(i, str)`, so live CSW
`MD_Keywords` objects become `[]`. Mapper never reads `record.keywords`. Other mappers already emit transitional
Investigation Comment `Keywords` for Search Hub via the API. Model stays `keywords: list[str]` under existing
`inspire-value-bounds`.

## Goals / Non-Goals

**Goals:**

- Correct ISO→`InspireRecord.keywords` extraction for OWSLib `MD_Keywords` and plain strings.
- Emit one deterministic `Keywords` Comment from those names.
- Align `docs/mappers/inspire.md` with behaviour.

**Non-Goals:**

- Nested keyword model (thesaurus / Anchor URI) — #603 / #441.
- Per-term Comments or OntologyAnnotation keywords.
- Protocol-table `Keywords` parameter on INSPIRE Study/Assay (Schema.org/Regal also have protocol params; not required
  for Search Hub Comment path).

## Decisions

1. **Keep `list[str]` names only** — Aggregate Comment needs labels; richer `Keyword` models would force bounds/docs
   churn without Search Hub benefit in this slice. Thesaurus/URI deferred.
   - Alternative: nested model now → rejected as scope creep for lock-in A.

2. **Parser walks `MD_Keywords.keywords[].name`** — Match OWSLib shape verified on BonaRes. Also accept legacy/test
   plain `str` items so existing unit fixtures keep working.
   - Alternative: only `MD_Keywords` → would break string-based tests without migration value.

3. **Mapper dedupe/sort like Schema.org** — Trim → drop empty → casefold dedupe (first spelling wins) → sort
   `(casefold, original)` → `", ".join`. Harvest-stable across CSW order noise.
   - Alternative: preserve source order → non-deterministic ARC hashes when OWSLib/list order shifts.

4. **Comment only, no OntologyAnnotation** — Matches API Comments lock-in (#417/#603). Existing hardcoded GEMET
   `OntologySourceReference` in `_add_ontology_sources` is unrelated and unchanged.

5. **Docs edit in same change** — `inspire-to-arc-mapping` treats `docs/mappers/inspire.md` as authoritative; table +
   stale GEMET NOTE must match the Comment MVP.

## Risks / Trade-offs

- **[Risk] Aggregate join vs commas inside labels** → Same known limitation as Regal/Schema.org; #604 / API per-term
  path is the fix. Do not invent a different separator for INSPIRE alone.
- **[Risk] Losing thesaurus/URI until #603** → Acceptable for Search Hub string keywords; document as deferred in
  proposal/non-goals.
- **[Trade-off] No Study protocol Keywords column** → Slightly less parity with Schema.org protocol tables; Comment is
  enough for dump `keywords`.

## Migration Plan

- Ship with next harvester release; no config flag. Re-harvest fills Comments; API already materializes `Keywords`.
- Rollback: revert parser/mapper; old behaviour was empty keywords (no worse than today).

## Open Questions

- None for this slice. Per-term / AGROVOC URI encoding deferred to #603.
