## Why

`GeneralSchemaOrgMapper` is self-documented as "EXAMPLE IMPLEMENTATION" — it
works but lacks a definitive spec for how Schema.org maps to ARC. As more
institutional repositories expose Schema.org JSON-LD (MyCoRe Solr, XML
Sitemaps, bioschemas catalogs), the mapping needs a production contract:
what gets mapped, how identifiers are chosen, what validation is required, and
how vocabulary extensions participate.

Without this spec, each new Schema.org source risks inconsistent mapping
behaviour and unstable Investigation identifiers across harvests.

## What Changes

- **New capability spec** `openspec/specs/schemaorg-to-arc-mapping/spec.md`
  defining the behaviour contract for Schema.org → ARC mapping.
- Covers: multi-dataset-per-graph handling, `@context` validation and
  normalization, vocabulary extension mechanism, deterministic identifier
  cascade, `DataDownload` distribution mapping, fail-closed on missing fields,
  deterministic multi-value ordering.
- Implementation will evolve `GeneralSchemaOrgMapper` (or a successor) to
  satisfy the spec; the spec itself is format-agnostic.

### Non-Goals

- SHACL/ShEx shape validation (allowlist `@context` only for v1).
- INSPIRE or Regal mapping changes (separate specs).
- Runtime harvest linter.
- YAML/JSON mapping DSL.
- `DataCatalog` as a standalone output (maps as a container of Datasets only).

## Capabilities

### New Capabilities

- `schemaorg-to-arc-mapping`: behaviour contract for mapping Schema.org
  `schema:Dataset` entities to ARC Investigation/Study/Assay components,
  including `@context` validation, vocabulary extensions, identifier cascade,
  `DataDownload` distribution handling, and deterministic ordering.

### Modified Capabilities

None — this is a new standalone capability. Existing `linked-data-mapper` and
`linked-data-harvesting` specs are not modified.

## Impact

- **Affected domains**: new `openspec/specs/schemaorg-to-arc-mapping/`.
- **Code**: `middleware/linked_data/.../linked_data_mapper/`
  (`general_schema_org_mapper.py`, `stable_graph.py`); `HtmlJsonLdDataset`
  for `@context` validation; unit tests under
  `middleware/linked_data/tests/unit/`.
- **Related**: opens `docs/schemaorg_mapping.md` (authoritative field tables).
- **Dependencies**: none new (rdflib, arctrl already in use).
- **Follow-up**: `docs/schemaorg_mapping.md` field tables; optional SHACL
  validation in a future change.
