## Why

BonaRes Knowledge Library (`fairagro/m4_rdi_portfolio#5`) now exposes a public schema.org/JSON-LD API, but its
`schema:Dataset` node carries almost no descriptive metadata: across all 828 catalogue records the Dataset node has
0 descriptions, 0 authors, 0 DOIs and 0 `url` values. Every one of those sits on the work node referenced via
`schema:isBasedOn` (828 authors, 797 DOIs, 811 urls, 741 abstracts). `GeneralSchemaOrgMapper` reads `isBasedOn`
nowhere, so mapping the catalogue as-is yields ARCs with a placeholder title, an empty description, no contacts and no
publication.

`schema:isBasedOn` is a core `CreativeWork` property and this use of it is semantically correct — a Knowledge Library
record genuinely *is* a dataset (extracted soil `Observation` nodes) derived from a publication. Any
literature-extraction repository could encode its records the same way, so treating "the descriptive metadata is one
`isBasedOn` hop away" as a generic Schema.org shape is justified, not an RDI-specific quirk.

## What Changes

- `ResourceView` gains an optional, ordered **fallback-subject chain**. A property read against a subject that yields
  nothing falls through to the next subject in the chain. Per-property, first-non-empty-wins; results are never merged
  across subjects.
- `GeneralSchemaOrgMapper` builds each Dataset's view with that Dataset's `schema:isBasedOn` targets as the chain, so
  description, contacts, `url`, `license` and the publication DOI are recovered for thin Dataset nodes without changing
  any existing call site.
- DOI resolution falls back on **no parsed DOI**, not merely on "no objects for the predicate" — a thin Dataset may
  carry a `schema:identifier` node that contains no DOI, which would otherwise block the chain.
- Any field resolved through the chain is recorded as an Investigation Comment, mirroring the existing `"Title Source"`
  treatment: a thin record MUST NOT be silently dressed up.

## Non-Goals

- **Title resolution.** The existing title cascade is unchanged. It resolves at `schema:name`, and a placeholder name
  (BonaRes emits `"Knowledge Library metadata for <title>"`) is a non-empty value that no general rule can recognise as
  a placeholder. That is an RDI-side defect, raised with the operator.
- **Keywords via `schema:about`.** The mapper still does not traverse `about` → `DefinedTerm`. BonaRes has no keyword
  literals anywhere, so the fallback chain cannot help; separate concern.
- **Transitive traversal.** The chain is one hop. An `isBasedOn` target's own `isBasedOn` is not followed.
- **Merging across subjects**, and any change to `Investigation.identifier` resolution.
- The BonaRes `bonares_klib` sitemap and dataset type — a separate follow-up change.

## Capabilities

### Modified Capabilities

- `stable-graph`: `ResourceView` property reads may resolve against an ordered fallback-subject chain.
- `schemaorg-to-arc-mapping`: Dataset metadata resolution falls back to `schema:isBasedOn` targets for otherwise-absent
  fields.

## Impact

- **Affected domains**: `openspec/specs/stable-graph/`, `openspec/specs/schemaorg-to-arc-mapping/`.
- **Code**:
  [`stable_graph.py`](../../../middleware/payload/src/middleware/payload/linked_data_mapper/stable_graph.py),
  [`general_schema_org_mapper.py`](../../../middleware/payload/src/middleware/payload/linked_data_mapper/general_schema_org_mapper.py);
  tests under [`middleware/payload/tests/`](../../../middleware/payload/tests/).
- **Behaviour change for existing sources**: a source gains values only where a field is currently empty *and* its
  Dataset has `schema:isBasedOn`. Sources without `isBasedOn` are bit-identical. This is the reviewable risk in this
  change and is covered by an explicit regression scenario.
- **API / config / dependencies**: none. No new configuration; the behaviour is unconditional.
- **Review**: architecture-level (shared mapper, affects every `schema_org_general` source) — request @Zalfsten.
