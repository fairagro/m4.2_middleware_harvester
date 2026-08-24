## Context

See proposal.md. `GeneralSchemaOrgMapper._extract_doi()` returns the first DOI from `_schema_objects(..., "identifier")`. `_resolve_investigation_identifier()` uses that value directly when present. Concurrent linked-data workers map records independently with no cross-record DOI visibility.

Observed cases:

| Pattern | Example | Symptom |
|---------|---------|---------|
| Multi-DOI, one URL | `00107508` → `10.3220/…` + `10.5281/zenodo.…` | Twin ARCs per run |
| One DOI, two URLs | `10.1594/PANGAEA.957630` on `00088718` + `00109919` | Duplicate identifier rejection |

## Goals / Non-Goals

**Goals:**

- Exactly one stable `Investigation.identifier` per logical OpenAgrar page across harvest runs.
- No duplicate-identifier upload failures for shared external DOIs within one harvest.
- All DOIs remain visible in mapped ARC metadata.
- Small diff aligned with existing mapper conventions.

**Non-Goals:**

- API-side changes, GitLab merge of existing twins, or OpenAgrar catalog cleanup.
- Registrar-specific priority lists beyond lexicographic canonical DOI rule.
- Changing Regal/INSPIRE paths.

## Decisions

1. **Run-level collision registry in `LinkedDataPlugin` (collect-then-map)**
   — Reasoning: collision resolution requires knowing all `(source_url, doi)` pairs in the batch before choosing identifiers. Concurrent map-as-you-fetch cannot detect cross-page collisions deterministically. Plugin buffers `(graph, source_url)` after fetch, builds `doi → set[source_url]`, derives `colliding_dois = {doi | len(urls) > 1}`, then maps each record with that set. Alternative considered: detect duplicates only in `upload.py` after mapping — rejected because ARC JSON is already wrong and API rejects too late. Alternative: first-wins during concurrent map — rejected as order-dependent across runs.

2. **Identifier decision chain (mapper)**
   — Reasoning: collision and multi-DOI are orthogonal. Order:
   1. Extract all DOIs, `source_url`, RDI ID (OpenAgrar: `openagrar_mods_*` from `/receive/{id}` URL).
   2. If any extracted DOI is in `colliding_dois` → `Investigation.identifier = RDI ID` when extractable.
   3. Else if multiple DOIs on this page → lexicographic minimum (`casefold`) as canonical DOI.
   4. Else if exactly one DOI → that DOI.
   5. Else existing URL / sanitized `source_url` fallbacks.
   6. Else fail closed (`ValueError` → `RecordProcessingError`).
   When step 2 applies, the shared external DOI(s) remain in Publication/Comments, not as primary identifier.

3. **Canonical multi-DOI rule: lexicographic minimum**
   — Reasoning: generic, testable, order-independent. For `00107508`, `10.3220/253-2025-54` < `10.5281/zenodo.15672440`, matching institutional-before-mirror intent without hard-coded registrars. Alternative: explicit OpenAgrar-before-Zenodo priority — rejected as RDI-specific maintenance.

4. **RDI ID format for OpenAgrar collision fallback**
   — Reasoning: use bare MyCoRe id `openagrar_mods_*` (not full sanitized URL) as `Investigation.identifier` — stable, human-readable, unique per page, already used in operator workflows. Extract via regex on Receive-URL; if collision detected but RDI ID not extractable, fall through to step 3/4/5 (canonical DOI or URL fallback) rather than inventing an id.

5. **Alternate DOI metadata**
   — Reasoning: non-canonical DOIs on the same page → Investigation Comment `Alternate Identifier`. When RDI ID is primary due to collision, the shared external DOI → existing Publication row (or Comment if no single canonical pick). Keeps PANGAEA/CRAN DOI grep-visible without owning `arc_id`.

6. **Extend `map_graph` with optional mapping context**
   — Reasoning: add `colliding_dois: frozenset[str] | None = None` (or a small `SchemaOrgMappingContext` dataclass) to `LinkedDataMapper.map_graph`; `RegalMapper` ignores it. Keeps ABC compatible with default `None` (= no collision override, current single-record behaviour in tests).

## Risks / Trade-offs

- **Collect-then-map buffers all graphs for a harvest batch** → higher peak memory on very large sitemaps; acceptable for OpenAgrar scale (~1k records). Mitigation: only enable two-phase path for Schema.org payload type.
- **Lexicographic min may pick unexpected DOI in edge cases** → explicit rule + tests; alternates preserved in Comments.
- **Existing twin ARCs not merged** → first stable harvest after deploy converges on one canonical path per page; orphans remain until manual cleanup.
- **Collision set is per harvest run** → same page always gets same RDI ID; shared DOI pages always diverge within and across runs once collision is detected in that batch.

## Migration Plan

- Deploy harvester only. No API or config changes.
- Rollback: revert plugin + mapper; non-deterministic DOI selection and duplicate errors resume.
