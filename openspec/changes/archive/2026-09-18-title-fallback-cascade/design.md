## Context

See proposal.md and PR #221. `_require_dataset_title` raised on missing
`schema:name` with no fallback. Real OpenAgrar records (issue #164) carry a
usable title under `headline` or `alternativeHeadline`, or only in the HTML
page's `<title>` / `citation_title` meta tag when the JSON-LD itself omits a
name — those records were being dropped entirely instead of harvested with a
recorded caveat.

## Goals / Non-Goals

**Goals:**

- Recover a title for records missing `schema:name`, without inventing one
  (`"Untitled"`) when nothing usable exists anywhere.
- Make every fallback traceable: which source won, on which record.
- Keep the HTML-title path cheap for the common case where `schema:name` is
  already present (most records).

**Non-Goals:**

- A harvester-report-level `WARNING` issue kind (needs a `fairagro-middleware-shared` release).
- Regal / INSPIRE title resolution.

## Decisions

1. **Cascade order: `name` → `headline` → `alternativeHeadline` (document
   order) → HTML title hint**
   — Reasoning: mirrors Schema.org's own field semantics (`headline` and
   `alternativeHeadline` are explicitly title-shaped fields); the HTML hint
   is last because it's outside the RDF graph entirely and least
   structured. `alternativeHeadline` picks the first non-empty entry in
   *document* order, not the alphabetically-sorted order `schema_texts()`
   normally returns, because the source list is meant to be read as an
   ordered list of alternatives, not a set.

2. **HTML title hint is `html_jsonld`-only and lazy**
   — Reasoning: only `html_jsonld` datasets fetch an HTML page at all; other
   dataset kinds have no page to extract a `<title>` from.
   `MappingContext.html_title` is a zero-arg callable
   (`Dataset.title_hint_from_cache`), not a precomputed value, so the extra
   `HTMLParser` pass only happens for the minority of records that actually
   reach that fallback branch — not on every harvested record.

3. **Fallback use is always recorded, never silent**
   — Reasoning: a title fallback changes what value ends up in
   `Investigation`/`Study`/`Assay` title; silently substituting it would make
   provenance debugging much harder. Every non-`schema:name` resolution adds
   a `"Title Source"` Investigation Comment and a WARNING log line naming
   the source.

4. **Never log or emit an rdflib blank-node label**
   — Reasoning: existing project-wide invariant
   (`assert_harvest_has_no_bnode_labels`, `stable_graph.py`). The title
   fallback's WARNING log identifies the subject by its IRI when it has one,
   else falls back to the resolved title itself — never `str(subject)`.

## Risks / Trade-offs

- Records that previously failed closed on missing `schema:name` now harvest
  successfully with a different title source; downstream consumers relying
  on the previous hard failure as a data-quality signal will instead see a
  `"Title Source"` Comment — this is the intended behavior change.
- `alternativeHeadline` document order depends on rdflib's iteration order
  for the underlying store, which is insertion-order for the in-memory store
  this codebase uses but is not a guaranteed RDF property in general.

## Migration Plan

- Deploy harvester only. No API or config changes. Rollback: revert the
  mapper/dataset/plugin changes; behavior reverts to fail-closed-only.
