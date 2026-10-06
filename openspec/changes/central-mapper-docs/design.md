# Design

## Context

See `proposal.md` for motivation. Today three mapping docs live at flat paths; PhenoRoam and `ckanext-dcat` have
OpenSpec domains and registered `DataMapper`s but no authoritative mapping Markdown. There is no `overlay_registry` in
current code — RDI quirks (for example OpenAgrar title fallback) largely live inside shared format mappers or harvest
context, not as separate mapper types. #140 already placed mappers beside config under `middleware.payload`.

## Goals / Non-Goals

**Goals:**

- Land `docs/mappers/` layout and Markdown conventions (base vs `rdi/` overlay).
- Move existing three docs; author missing base docs from code + specs.
- Audit Schema.org / Regal / INSPIRE docs against specs and implementations; fix doc/spec drift in-tree.
- Normative OpenSpec hooks so every mapping domain points at `docs/mappers/…`.
- Document future Markdown→code generation as intent only.

**Non-Goals:**

- Implementing a generator or registry fields for `builds_on`.
- Inventing RDI overlay files without a code/config delta to document.
- Softening parser/mapper separation (context allowlists stay on parser config; see #247 closed as superseded by #391).
- Documenting the `linked_data:` protocol plugin (see #296); mapping docs are payload-mapper files only.
- Invented placeholder titles (`Untitled`) as a mapping strategy.

## Decisions

1. **Layout names** — `docs/mappers/{schemaorg,regal,inspire,phenoroam,ckanext-dcat}.md` and
   `docs/mappers/rdi/<rdi>_<base>.md`. Reasoning: matches #170 and registry-ish mapper identities without encoding
   `MapperType` enum strings as filenames. Alternatives: keep `*_mapping.md` suffixes (noisier); one file per
   `MapperType` enum value including `_general` (couples docs to registry keys).

2. **No legacy stubs** — delete/relocate old `docs/*_mapping.md`; update all live references. Reasoning: avoids dual
   sources of truth. Alternatives: leave redirect stubs (extra maintenance).

3. **Missing docs from code first** — for PhenoRoam and `ckanext-dcat`, derive field tables from the mapper
   implementation and existing OpenSpec requirements, then reconcile. Reasoning: no prior Markdown exists; code+tests
   are the behaviour oracle. Alternatives: invent tables from specs only (weaker for edge cases only in code).

4. **Audit existing three** — compare `docs` ↔ OpenSpec domain ↔ mapper module; fix docs when they lag intentional
   behaviour; fix specs only when the implementation contract text is wrong; open a linked follow-up if code itself must
   change. Reasoning: this issue is documentation/architecture, not a silent behaviour PR.

5. **RDI overlays opportunistic** — create `rdi/` entries only when a concrete RDI delta is identifiable in shipped
   config or code comments/tests; otherwise leave `rdi/` with README guidance only. Reasoning: no overlay classes today;
   empty overlay files would invent contracts. Alternatives: always create OpenAgrar/Publisso stubs (rejected).

6. **Markdown schema (MVP)** — YAML front matter (`payload_kind`, optional `mapper_id`, for overlays `builds_on`) plus
   fixed section headings (Identity, Investigation, Study, Assay, Contacts, Fallbacks, Refusal/Skip). Full generator
   column schemas are documented as future constraints in the README, not enforced by tooling yet. Reasoning: unlocks
   layout without blocking on a generator design. Alternatives: full tabular DSL now (out of scope).

7. **Code generation** — document in `docs/mappers/README.md` and `mapper-docs` that Markdown is the intended generator
   input; no implementation. Reasoning: lock-in from #170 explore.

8. **Thin README** — index + schema + generation note only. Reasoning: specs own behaviour; README is navigation.

## Risks / Trade-offs

- **[Risk] Large link churn misses archived OpenSpec paths** → Mitigation: update live `openspec/specs/`, principles,
  READMEs, and product docs; leave archived change history as historical unless a live link breaks.
- **[Risk] Audit finds real code bugs** → Mitigation: document in tasks; fix only clear doc/spec mismatches here; split
  behaviour fixes via `/create-issue` (`relation: linked`).
- **[Risk] Authoring PhenoRoam/ckanext docs is large** → Mitigation: mirror section shape of existing mapping docs; keep
  field tables faithful to code, not aspirational.
- **[Trade-off] Overlay docs without overlay classes** may later need renaming when `mapper.type` overlays land →
  Acceptable; `builds_on` stays docs-only until then.

## Migration Plan

1. Add `docs/mappers/` scaffold + README schema.
2. `git mv` the three existing mapping docs to new names; fix references.
3. Author `phenoroam.md` and `ckanext-dcat.md` from code/spec.
4. Run the three-way audit; apply doc/spec fixes.
5. Add optional `rdi/` docs only if deltas are found.
6. Land OpenSpec deltas; update Purpose lines on existing mapping specs to the new paths during apply.

## Open Questions

None blocking. Optional later: whether `mapper_id` front matter must equal `MapperType` string values once a generator
exists.
