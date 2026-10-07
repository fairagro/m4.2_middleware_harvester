# Proposal

## Why

Mapper documentation is scattered under flat `docs/*_mapping.md` paths and incomplete: Schema.org, Regal, and INSPIRE
have authoritative field docs, but productive mappers such as PhenoRoam and CKAN `ckanext-dcat` only have OpenSpec
requirements without matching mapping tables. RDI-specific deltas are not yet documented as overlay docs. We need one
layout under `docs/mappers/` (base + optional `rdi/` overlays), aligned with the shared `middleware.payload` mapper
layer (#140, closed), so specs link to mapping docs instead of restating field tables and so future code generation has
a stable input shape (#170).

## What Changes

- Introduce `docs/mappers/` with base mapper docs and optional `docs/mappers/rdi/` overlay docs (`builds_on` a named
  base).
- **Relocate** existing `docs/schemaorg_mapping.md`, `docs/regal_mapping.md`, and `docs/inspire_mapping.md` into the new
  layout; update OpenSpec / README / comment links. **No** stub files left at the old paths.
- **Author missing base mapping docs from current code + specs** for mappers that already ship without a mapping `.md`
  (at least `phenoroam` and `ckanext-dcat`).
- **Audit** existing Schema.org / Regal / INSPIRE mapping docs against their OpenSpec domains and mapper
  implementations; fix doc or spec mismatches found in this change (prefer aligning docs to intentional code+spec
  behaviour; raise a follow-up only if behaviour itself must change).
- Document a minimal Markdown schema (front matter / required sections) for base vs RDI-override docs; speak RDF or
  typed records (`inspire_record`, `phenoroam_record`), not StableGraph.
- Capture in OpenSpec that mapping `.md` files under `docs/mappers/` are the authoritative source→ARC contract and the
  **intended** input for a future code generator. **Do not** implement automatic code generation in this change.
- Add a thin `docs/mappers/README.md` index only (no architecture essay).
- RDI overlay files: create only where code or shipped config encodes a real RDI-specific delta relative to a base
  mapper; do not invent empty overlays. Overlay classes are not a prerequisite — docs may describe config/context-driven
  deltas.

## Capabilities

### New Capabilities

- `mapper-docs`: Layout, Markdown schema (base vs RDI override), authority of `docs/mappers/*.md`, and documented
  (non-implemented) code-generation input contract.

### Modified Capabilities

- `schemaorg-to-arc-mapping`: Point authoritative source to `docs/mappers/schemaorg.md`; adjust only if the audit finds
  requirement/doc drift that must be reflected in the implementation contract.
- `regal-to-arc-mapping`: Same for `docs/mappers/regal.md`.
- `inspire-to-arc-mapping`: Same for `docs/mappers/inspire.md`.
- `phenoroam-to-arc-mapping`: Add authoritative mapping-doc link to the new `docs/mappers/phenoroam.md`.
- `ckanext-dcat-to-arc-mapping`: Add authoritative mapping-doc link to the new `docs/mappers/ckanext-dcat.md`.

## Impact

- Docs and OpenSpec link updates across mapping domains, principles narrative, READMEs, and code comments that cite old
  paths.
- **Mapper fail-closed:** Regal and `ckanext_dcat` MUST NOT invent `"Untitled"` / `untitled`; missing required title
  (after documented source cascade) fails mapping. Same rule in `openspec/principles.md`.
- Non-goals: implementing #140 again; implementing a Markdown→code generator; materializing full RDI docs that duplicate
  an entire base; moving StableGraph semantics into mapping docs; coupling parser config to mapper type; documenting or
  extending the `linked_data:` plugin (removed after #296 — mapping docs target `middleware.payload` only).
