## Context

`GeneralSchemaOrgMapper` already works and is tested. It handles:
- Dual http/https Schema.org namespaces
- Blank-node label suppression
- Language-aware literal selection (en > de > untagged > other)
- Identifier cascade (harvest context → URL → DOI)
- Person given-name validation

What it lacks: a definitive spec, multi-dataset-per-graph handling,
`@context` validation, vocabulary extension support, and `DataDownload`
distribution mapping. This change fills those gaps and documents the
existing identifier cascade as a formal precedence rule.

## Goals / Non-Goals

**Goals:**

- Formalize the existing Schema.org → ARC mapping as a behaviour contract.
- Add `@context` validation with a minimal allowlist (no full JSON-LD context
  expansion).
- Support vocabulary extensions (Bioschemas, etc.) via declared extension
  namespaces in the existing `StableGraphPolicy.term_namespaces`.
- Handle multiple `schema:Dataset` entities per graph (yield multiple outputs).
- Map `schema:DataDownload` distributions to Assay output columns.
- Document the identifier cascade precedence rule (currently implicit).

**Non-Goals:**

- SHACL/ShEx validation (allowlist is sufficient for v1).
- `DataCatalog` as a standalone output — it's a container, not a dataset.
- INSPIRE or Regal mapping changes.
- Moving the identifier cascade or publisher-invert policy into `stable_graph`.

## Decisions

1. **Multi-dataset = multiple yields from the same `map_graph` call**
   — Reasoning: a single page may contain multiple `schema:Dataset` entities
   (e.g., DataCatalog with hasPart). The generator contract already supports
   multiple yields. Changing `map_graph` to `Iterable[HarvestedArc]` or
   returning a list is the cleanest path.
   — Alternatives considered: one graph = one dataset (current discovery
   assumption); separate the datasets before calling map_graph.

2. **`@context` validation in the dataset fetcher, not the mapper**
   — Reasoning: the fetcher has the raw JSON-LD text; the mapper only gets an
   rdflib Graph (context lost). Validating before parsing avoids double-parsing.
   The allowlist is a small frozen set in code — no local cache needed.
   — Alternatives considered: validate inside the mapper (requires raw JSON);
   use rdflib's jsonld parser hooks (fragile).

3. **Extension namespaces via `StableGraphPolicy.term_namespaces` (already exists)**
   — Reasoning: `term_namespaces` already powers `schema_objects`,
   `schema_is_type`, etc. Adding Bioschemas or other extensions is just
   declaring more namespaces — no API change needed. The mapper's
   `_stable_wrap` override already passes vocabulary-specific namespaces.
   — Alternatives considered: separate `extension_namespaces` field;
   YAML-based extension config.

4. **Identifier cascade stays implicit in the mapper — spec documents the rule**
   — Reasoning: the cascade is mapper policy (not RDF access policy). The spec
   documents the precedence; the implementation composes it from `doi()`,
   `http_iri()`, and `resolve_harvest_source_identifier()` bricks.
   — Alternatives considered: move cascade into StableGraph (couples RDF access
   to harvest identity); expose cascade as a separate utility.

5. **`DataDownload` → Assay output columns**
   — Reasoning: `schema:distribution` → `schema:DataDownload` with
   `contentUrl`/`encodingFormat` is the natural mapping for dataset file
   access. Each distribution becomes an output column in the Measurement Assay
   table (matching current Assay table structure).
   — Alternatives considered: map as Investigation comments (loses structured
   access); map as separate Assay per distribution (too many Assays).

6. **`DataCatalog` as container, not output**
   — Reasoning: a DataCatalog is a collection of Datasets; the ISA model
   doesn't have a "Catalog" concept. Mapping each member Dataset separately
   is the correct semantic mapping.
   — Alternatives considered: skip DataCatalogs entirely (loses information);
   map as Investigation comment (loses structure).

## Risks / Trade-offs

- **[Risk] Multi-dataset `map_graph` signature change breaks Regal** →
  Mitigation: Regal mapper already uses one graph = one dataset; signature
  change is backward compatible (list of one). Add adapter if needed.
- **[Risk] `@context` allowlist too restrictive for unknown sources** →
  Mitigation: log warning for unknown contexts, allow opt-out via config
  for trusted sources; fail-closed by default.
- **[Trade-off] Allowlist vs full JSON-LD context expansion** → Accepted:
  allowlist is simpler, faster, and sufficient for Schema.org + known
  extensions. Full expansion adds complexity with minimal benefit for v1.

## Migration Plan

1. Add `@context` validation in `HtmlJsonLdDataset.fetch()` with allowlist
   for Schema.org + Bioschemas.
2. Extend `_find_dataset_subject` → `_find_dataset_subjects` returning all
   `schema:Dataset` entities; update `_map_graph` to yield multiple outputs.
3. Add `DataDownload` → Assay output column mapping in `_create_assay_table`.
4. Write `docs/schemaorg_mapping.md` field tables (authoritative source).
5. Run linked_data unit tests + ruff; confirm no regressions.

Rollback: revert the change branch; no config or API-server migration.
