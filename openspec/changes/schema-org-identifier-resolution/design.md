## Context

See proposal.md. `GeneralSchemaOrgMapper._extract_doi()` returned the first DOI from `_schema_objects(..., "identifier")`. `_resolve_investigation_identifier()` used that value directly when present. DOI is not a stable per-page key: one page can list multiple DOIs (order-dependent selection), and one DOI can appear on multiple harvested pages (duplicate `arc_id`).

Observed cases:

| Pattern | Example | Symptom |
|---------|---------|---------|
| Multi-DOI, one URL | `00107508` → `10.3220/…` + `10.5281/zenodo.…` | Twin ARCs per run |
| One DOI, two URLs | `10.1594/PANGAEA.957630` on `00088718` + `00109919` | Duplicate identifier rejection |

## Goals / Non-Goals

**Goals:**

- Exactly one stable `Investigation.identifier` per harvested page across harvest runs.
- No duplicate-identifier upload failures for shared external DOIs.
- All DOIs remain visible in mapped ARC metadata.
- Small diff aligned with existing mapper conventions; no per-run collision registry in the plugin.

**Non-Goals:**

- API-side changes, GitLab merge of existing twins, or OpenAgrar catalog cleanup.
- Registrar-specific priority lists beyond lexicographic canonical DOI rule for Publication metadata.
- Changing Regal/INSPIRE paths.

## Decisions

1. **Harvest-source-first identifier (Option C)**
   — Reasoning: the harvest unit is the discovered dataset page, not the DOI. Order:
   1. `harvest_source_id` from the sitemap/discovery layer when supplied (e.g. MyCoRe Solr `id` on `UrlDiscoveryResult`).
   2. Sanitized discovered page URL when `source_url` is an `http(s)` URI.
   3. Canonical `http(s)` URL from `schema:url`, then `schema:sameAs`, then Dataset `@id` when it is an `http(s)` IRI (sanitized).
   4. Single extracted DOI as last resort.
   5. Fail closed.
   RDI-specific id extraction belongs in sitemap implementations, not mapper code or harvester config regex.

2. **DOIs always in Publication/Comments, not primary when source exists**
   — Reasoning: when `source_url` or a graph URL is available, DOIs populate Publication (canonical pick) and `Alternate Identifier` Comments (non-canonical on the same page). Shared external DOIs on different pages no longer collide because each page keeps its own harvest key.

3. **Canonical multi-DOI rule: lexicographic minimum for Publication only**
   — Reasoning: generic, testable, order-independent. For `00107508`, `10.3220/253-2025-54` < `10.5281/zenodo.15672440`. Applies to Publication DOI selection, not `Investigation.identifier`, when `source_url` is present.

4. **Plugin passes `source_url` only; no collect-then-map**
   — Reasoning: harvest-source-first policy makes a per-run DOI collision set redundant. The plugin continues concurrent fetch + map with `map_graph(graph, source_url=...)`.

## Risks / Trade-offs

- **Identifier semantics shift** — existing ARCs keyed by DOI will not match new harvests for pages where DOI was previously primary; acceptable: API path is `sha256(identifier + rdi)` and the fix targets stability going forward.
- **Lexicographic min may pick unexpected Publication DOI** → explicit rule + tests; alternates preserved in Comments.
- **Existing twin ARCs not merged** → orphans remain until manual cleanup.
- **Graphs without `source_url` still fall back to DOI** → unit tests and non-HTML sources unchanged.

## Migration Plan

- Deploy harvester only. No API or config changes.
- Rollback: revert mapper; non-deterministic DOI selection and duplicate errors resume.
