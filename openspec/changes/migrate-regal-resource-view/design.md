## Context

See `proposal.md` for motivation (`#147`). After `#138`, `StableGraph` /
`ResourceView` exist and Schema.org uses them via `_stable_wrap` + per-call
`_SchemaOrgRun`. `RegalMapper` still discards `stable` (`_ = context, stable`)
and keeps private `_str` / `_strs` / `_term_text` / `_labelled_nodes`. `#144`
made those helpers BNode-safe for funding/opaque paths, but multi-value order
and contact iteration remain rdflib-order dependent. Scope locked in explore:
**delete the private hygiene stack** (tier B), not hot-path-only patches.

## Goals / Non-Goals

**Goals:**

- Wire Regal `_stable_wrap` with `label_predicates=(SKOS.prefLabel,)`.
- Route all ARC-bound field reads through ResourceView; delete private string
  helpers.
- Deterministic contact / multi-value / opaque-comment ordering.
- Regression + permutation + concurrent shared-mapper tests for Regal.

**Non-Goals:**

- New StableGraph unknown-predicate API; opaque walk stays in the mapper.
- Changing ResearchData subject selection (`subjects[0]` / contentType scan).
- Implementing `contributorOrder` Contact sorting.
- Field-table changes in `docs/regal_mapping.md`.
- `#140` payload package move; archiving `stable-graph-resource-view`.

## Decisions

1. **Done = delete private RDF string helpers (tier B)**
   — Reasoning: Hot-path-only migration leaves a second hygiene stack and
   recreates `#144`-class bugs. Acceptance criteria on `#147` require Regal
   reads through ResourceView. One-time order/pick differences vs today’s
   `graph.value` / unsorted `_strs` are accepted; success is deterministic
   under JSON-LD / BNode permutation, not bit-identity with prior arbitrary
   order.
   — Alternatives considered: contacts+funding+opaque only (rejected);
   also invent StableGraph opaque API + stable subject pick (deferred).

2. **Per-call run holder; StableGraph never on `self`**
   — Reasoning: Same concurrent `asyncio.to_thread` constraint as Schema.org
   (`linked-data-mapper` StableGraph call-scoped requirement). A frozen
   `_RegalRun(stable)` (or equivalent) mirrors `_SchemaOrgRun` without storing
   session state on the shared mapper instance.
   — Alternatives considered: thread `stable` through every private method
   without a run type (allowed by spec, noisier); store wrap on `self` (forbidden).

3. **Wrap policy: `skos:prefLabel` labels, no Schema.org term namespaces**
   — Reasoning: Regal labelled nodes use SKOS; Schema.org http/https aliases
   would be unused noise. `StableGraph.wrap(label_predicates=…)` already
   supports this without API growth.
   — Alternatives considered: share Schema.org namespaces (misleading);
   hard-code SKOS only inside Regal helpers (defeats shared labelled()).

4. **Opaque comments remain mapper-local**
   — Reasoning: Filtering `_KNOWN_PREDICATES` and Comment naming is Regal ARC
   policy. Sort `(predicate IRI, object display text)` using StableGraph
   `object_text` / `sort_key` so order is harvest-stable without a new
   StableGraph surface.
   — Alternatives considered: `ResourceView.unknown_texts(known=…)` in this
   change (YAGNI until a second vocabulary needs it).

5. **Keep nested joinedFunding policy in the mapper**
   — Reasoning: Prefer `joinedFunding` over flat funding fields is Regal
   mapping rule (`docs/regal_mapping.md`). Compose child `ResourceView`s for
   program/project/funder strings; do not encode joined vs flat inside
   StableGraph.
   — Alternatives considered: generic “funding shape” helper in StableGraph
   (wrong layer).

6. **`#144` superseded, tests retained**
   — Reasoning: Behavioural BNode-safe funding/opaque requirements already in
   `regal-to-arc-mapping` stay; implementation ownership moves to ResourceView.
   Delete duplicated `_term_text` once call sites use `text` / `labelled` /
   `object_text`.
   — Alternatives considered: leave helpers as thin wrappers (fails “delete
   hygiene stack” lock).

## Risks / Trade-offs

- **[Risk] One-time Publisso content-hash churn** when singular picks /
  multi-value order change → Mitigation: expected; document in PR; verify
  second harvest is stable on draven after deploy.
- **[Risk] Behaviour drift vs existing Regal unit fixtures** → Mitigation:
  keep mapping-rule tests green; add permutation fixtures; adjust only where
  old assertions encoded rdflib accident order.
- **[Risk] Incomplete migration leaves a stray `graph.value`** → Mitigation:
  tasks include a grep gate for `_str` / `_strs` / `_term_text` /
  `_labelled_nodes` removal and review of remaining `graph.` uses.
- **[Trade-off] Opaque sort key may differ from Schema.org comment order
  policy** → Acceptable; Regal-only until a shared unknown-predicate API exists.

## Migration Plan

1. Implement wrap + run holder; port field access; delete helpers.
2. Add / extend unit tests (funding BNode, opaque, contact order, concurrent).
3. Land behind normal linked_data CI; deploy; spot-check Publisso re-harvest
   (no `has_changes` solely from `N…` or reshuffled contacts on unchanged
   records after the first post-deploy sync).

## Open Questions

None that block implementation; scope B is locked.
