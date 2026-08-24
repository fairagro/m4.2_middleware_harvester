## Why

Schema.org mapping for OpenAgrar currently picks the first DOI from non-deterministic rdflib iteration order. That causes **two distinct failure modes**:

**A) Multi-DOI on one page** — e.g. `openagrar_mods_00107508` lists `10.3220/253-2025-54` and `10.5281/zenodo.15672440`. Different harvest runs pick different `Investigation.identifier` values → different `arc_id = sha256(identifier:rdi)` → twin ARCs (`ecb3cd72…` vs `57efeaf7…`) that alternate updates.

**B) One DOI on multiple pages** — e.g. PANGAEA DOI `10.1594/PANGAEA.957630` on both `openagrar_mods_00088718` and `openagrar_mods_00109919`. Both pages map to the same identifier → API client rejects the second with `Duplicate ARC identifier`.

The Middleware API hashes whatever identifier the harvester sends; the fix belongs in harvester identifier resolution, not API-side normalization.

## What Changes

- Extend `GeneralSchemaOrgMapper` identifier resolution with a **testable decision chain**: DOI collision → RDI-specific ID; else multi-DOI → deterministic canonical DOI; else single DOI; else existing URL/RDI fallbacks; else fail closed.
- **Run-level DOI collision registry** in the linked-data plugin: before final mapping, collect `(source_url → DOIs)` for the harvest batch and mark DOIs shared by more than one `source_url` as colliding.
- **OpenAgrar RDI ID extraction** from MyCoRe Receive-URLs (`openagrar_mods_*`) when collision fallback applies.
- **Preserve all DOIs as metadata** (Publication for canonical; `Alternate Identifier` Comments for others); external DOI remains visible when RDI ID becomes primary identifier.
- Unit tests for multi-DOI stability, permuted identifier order, cross-page DOI collision, single-DOI regression, and sorcering-style pairs.

## Non-Goals

- Middleware API hash or duplicate-detection changes.
- GitLab cleanup of existing twin or duplicate-keyed ARCs.
- OpenAgrar source-data deduplication.
- INSPIRE / Regal identifier logic.
- Broader Schema.org determinism (keywords, authors) unless directly coupled.
- Future `ResourceView` API (issue #138) — keep this a focused mapper/plugin change.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `linked-data-mapper`: deterministic multi-DOI selection; RDI-ID fallback on DOI collision; alternate DOI metadata retention.
- `linked-data-harvesting`: plugin MUST build a per-run DOI collision set and pass it into Schema.org mapping.

## Impact

- **Affected domains**: `openspec/specs/linked-data-mapper/`, `openspec/specs/linked-data-harvesting/`.
- **Code**: [`general_schema_org_mapper.py`](middleware/linked_data/src/middleware/linked_data/linked_data_mapper/general_schema_org_mapper.py), [`plugin.py`](middleware/linked_data/src/middleware/linked_data/plugin.py), [`linked_data_mapper.py`](middleware/linked_data/src/middleware/linked_data/linked_data_mapper/linked_data_mapper.py) (ABC signature for mapping context); tests under [`middleware/linked_data/tests/`](middleware/linked_data/tests/).
- **API / config / dependencies**: none.
