## Context

See `proposal.md` for motivation ([#144](https://github.com/fairagro/m4.2_middleware_harvester/issues/144)).
`stabilize-regal-opaque-comments` already skips unlabelled blank nodes in opaque Comments, OAI/label helpers, and `_labelled_nodes`. `RegalMapper._str` / `_strs` still do `str(value)` / `str(obj)`, and `_funding_values` uses them for `fundingProgram` / `projectId` (flat and joined). `GeneralSchemaOrgMapper._strs` already uses `_stable_object_text` (BNode → `schema:name` or skip).

## Goals / Non-Goals

**Goals:**

- Make Regal `_str` / `_strs` BNode-safe so funding (and other callers) cannot persist parser-local labels.
- Keep joined-vs-flat funding preference unchanged.
- Prove stability with unit tests matching #144 acceptance criteria.

**Non-Goals:**

- Extracting a shared Schema.org/Regal helper in this change.
- Changing API content-hash volatile-field lists.
- Reworking funding mapping beyond blank-node safety.

## Decisions

### Harden `_str` / `_strs` (not only `_funding_values`)

**Choice:** Fix the primitives so every caller inherits blank-node safety.

**Reasoning:** Call-site-only fixes left funding broken after the opaque-comment work; systemic helper hardening matches Schema.org’s `_strs` approach and closes the class of bug. Literals/URIRefs (title, DOI, dates) keep current behaviour.

**Alternatives considered:** Patch only `_funding_values` (smaller diff, leaves footgun); share one helper with Schema.org now (needs label strategy parameter — defer).

### Blank-node label source: `skos:prefLabel`

**Choice:** For Regal blank nodes, resolve display text via `skos:prefLabel` only; if missing, skip.

**Reasoning:** Matches existing Regal labelled-node / license / opaque patterns and `docs/regal_mapping.md`. Schema.org’s `schema:name` is the wrong vocabulary here.

### Omit vs placeholder when unlabelled

**Choice:** Omit the value (no Funding Program / Project ID parameter from that object).

**Reasoning:** Same as opaque Comments; placeholders would still be wrong metadata. Losing a rare unlabelled funding facet is preferable to hash churn.

### `_str` when `graph.value` returns a BNode

**Choice:** Treat the object like `_strs`: if BNode, return prefLabel or `None` — never `str(BNode)`.

**Reasoning:** Joined path uses `_str(graph, node, REGAL.fundingProgramJoined)` where the object itself may be a BNode.

## Risks / Trade-offs

- **[Risk] Rare funding facets with only unlabelled BNodes disappear from ARC** → accepted; those values were never harvest-stable.
- **[Risk] Behaviour change if any code relied on `str(BNode)`** → none intended; such values were bugs.
- **[Trade-off] No shared Schema.org helper yet** → slight duplication; follow-up if desired.

## Migration Plan

1. Implement safe `_str` / `_strs`; keep `_funding_values` structure.
2. Add unit tests (BNode funding with/without prefLabel; dual-map stability).
3. Deploy harvester; confirm Publisso re-harvests no longer flip `has_changes` solely due to `N…` funding/project fields.

## Open Questions

None blocking; scope is option A from exploration (#144).
