# Mapper documentation

Authoritative source→ARC mapping tables for productive `DataMapper`s live here. OpenSpec mapping domains link to these
files and MUST NOT duplicate field tables. Layout contract:
[`openspec/specs/mapper-docs/`](../../openspec/specs/mapper-docs/).

## Layout

```text
docs/mappers/
  README.md                 # this index
  schemaorg.md              # base: rdf_graph / Schema.org
  regal.md                  # base: rdf_graph / Regal
  inspire.md                # base: inspire_record
  phenoroam.md              # base: phenoroam_record
  ckanext-dcat.md           # base: rdf_graph / CKAN ckanext-dcat DCAT-AP
  rdi/
    <rdi>_<base>.md         # optional RDI overlay (deltas only)
```

## Front matter (MVP)

Base documents:

```yaml
---
payload_kind: rdf_graph # or inspire_record | phenoroam_record
mapper_id: schema_org_general # optional; registry key when useful
---
```

RDI overlays under `rdi/`:

```yaml
---
payload_kind: rdf_graph
builds_on: schemaorg # base filename without .md
mapper_id: # optional future overlay registry key
---
```

Overlay files MUST list only deltas relative to `builds_on` (overrides, extra conventions, disabled base rules, extra
refusal/skip rules). Naming: `<rdi>_<base>.md` (e.g. `openagrar_schemaorg.md`).

## Required sections

**Base:** Identity · Investigation · Study · Assay · Contacts · Fallbacks · Refusal / skip rules (plus payload-specific
tables as needed).

**Overlay:** `builds_on` · Overrides · Additional source conventions · Disabled base rules · Additional refusal rules.

Documents speak RDF predicates or typed-record fields, not StableGraph APIs.

For required title/identifier cascades, mappers MUST NOT invent placeholder strings (`Untitled`, `untitled`, …); refusal
is fail closed. That rule targets mapper-invented fallbacks, not source-supplied placeholders the RDI sent. Those are
configured per repository (`inspire.placeholders` for INSPIRE, `mapper.placeholders` for the linked-data mappers; #437,
#459), and each document states its contract in a `Source placeholders` section without listing per-RDI strings. These
files document `middleware.payload` DataMappers, not the `linked_data:` plugin key.

## Future code generation

These Markdown files are the **intended** input for a future Markdown→mapper code generator. No generator is implemented
in this repository yet; until then humans and agents keep code, OpenSpec requirements, and these docs aligned manually.
