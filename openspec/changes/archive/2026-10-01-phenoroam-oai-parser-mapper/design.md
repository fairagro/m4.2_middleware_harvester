# Design

## Context

See proposal.md for motivation. Lock-ins from issue-fixer explore (#361):

1. Intermediate = Pydantic record model (Option A), not DOM-in-payload and not Schema.org.
2. Registry keys: `parser.type: phenoroam_xml`, `mapper.type: phenoroam_general`.
3. Contacts: shared `split_display_name` + `person-contact-given-name` policy (same as INSPIRE / Schema.org).
4. Identifier: prefer unique `itemUUID`; else landing URL — not DOI-driven.
5. Full ARC depth Investigation / Study / Assay + annotation tables; **no datafile Outputs** (#353).

`oai_pmh` already yields `XmlDiscoveryResult` with inline `<metadata>` for each ListRecords entry when configured with
`metadata_prefix: phenoroam`.

## Goals / Non-Goals

**Goals:**

- Parse native `pr:metadataDataset` into a typed intermediate owned by `middleware.payload` or colocated models imported
  by both parser and mapper without creating a plugin package for PhenoRoam.
- Map that intermediate to a valid ARC skeleton with Investigation/Study/Assay and annotation tables for metadata that
  has no corresponding file payload.
- Keep plugin contract: `oai_pmh` + sibling `parser` / `mapper` only.

**Non-Goals:**

- Geonetwork CSW / DCAT / REST.
- Fabricated Raw/Processed Data File entities or datafile Outputs (#353).
- Harvesting actual bytes from `pr:itemLink` URLs.
- EPrints / other OAI vocabularies.

## Decisions

1. **`PayloadKind.phenoroam_record` + Pydantic `PhenoroamRecord`** — Parser emits
   `ParsedPayload(kind=phenoroam_record, value=PhenoroamRecord, identifier=…)`. Mapper `accepts` that kind.
   _Alternative:_ DOM bytes in payload — rejected (lock-in A; harder tests). _Alternative:_ force `rdf_graph` — rejected
   (not RDF).

2. **Models live under `middleware.payload` (or `middleware.payload.phenoroam`)** — Same ownership as Regal/Schema.org
   vocabulary types; parser in `middleware.parsing` depends on payload for the model type (or parsing owns a thin DTO
   that payload re-exports — prefer one Pydantic model in payload that parsing constructs). _Alternative:_ models only
   in parsing — rejected (mapper would import parsing, forbidden by principles).

3. **XML parse with defusedxml** — Match OAI harvest path hardening; no network entity expansion. Namespace
   `http://www.phenorob.de/` (`pr:`). Fail closed if root is not `metadataDataset` / missing required title-like fields
   per SemanticError policy analogous to INSPIRE (decide exact required set in apply: at least UUID or title).

4. **Identifier resolution** — `itemUUID` if non-empty after trim (treat as unique within PhenoRoam); else constructed
   landing URL `https://phenoroam.phenorob.de/geonetwork/srv/eng/catalog.search#/metadata/{uuid-or-oai-id}`. Never
   require DOI. Pass through `sanitize_identifier` like other mappers.

5. **Contacts** — Map `pr:blockPerson` / responsible + other contacts via `split_display_name`. Empty given name → fail
   closed for person-like rows or Comment path consistent with existing policy (same helpers as INSPIRE/Schema.org; no
   PhenoRoam-specific name heuristics).

6. **Study / Investigation nesting** — `pr:blockStudyParent` / `pr:blockStudy` / `pr:blockInvestigation` → ARC Study and
   Investigation titles/descriptions. Assay carries process/annotation tables for keywords, license/rights, bbox, and
   optional **comments** listing remote datafile URLs as metadata strings — **not** ISA Data File / Output entities
   (#353).

7. **Registry names** — `phenoroam_xml` / `phenoroam_general` (aligned with `schema_org_general` / `regal_general`).

## Risks / Trade-offs

- **[Risk] `pr:` schema variance across records** → Mitigation: fixture from live ListRecords; optional blocks
  fail-soft; required fields fail closed with clear ParserError / mapping error.
- **[Risk] Broken thumbnail / attachment hosts (`phenoroam.phenorob.de:`)** → Mitigation: require http(s) + non-empty
  hostname when emitting URL-shaped comments; keep PhenoRoam's empty-port typo (`host:`) as-is (clients treat empty port
  as scheme default) so live datafile `itemLink` values are not dropped.
- **[Risk] Empty given name on `itemName`** → Mitigation: shared person-contact policy; record-level failure or Comment,
  never empty-given Person.
- **[Trade-off] No file Outputs** → Operators see metadata-only ARCs; data links only as comments/annotations until a
  future download/harvest feature exists.

## Migration Plan

Additive registries + example config. Existing RDIs unchanged. Rollback: remove PhenoRoam repo entry from config.
