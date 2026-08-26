## Why

Publisso/Regal harvests still write parser-local rdflib blank-node labels (`N` + 32 hex) into **Funding Program** / **Project ID** because `RegalMapper._str` / `_strs` use bare `str(value)`. Those labels change every JSON-LD parse, so the Middleware API sees `has_changes=True` and re-pushes to DataHub even when the dataset is unchanged. Opaque-comment paths were hardened earlier; funding still uses the unsafe helpers.

Tracked as GitHub [#144](https://github.com/fairagro/m4.2_middleware_harvester/issues/144).

## What Changes

- Harden `RegalMapper._str` / `_strs` so they never return `str(BNode)`: Literals and URIRefs stringify as today; blank nodes contribute only via `skos:prefLabel` (or are skipped).
- Ensure `_funding_values` (joined and flat `fundingProgram` / `projectId` paths) only emits stable labels/URIs.
- Audit other `str(obj)` on graph nodes in `RegalMapper` that could reintroduce the leak.
- Add regression tests: funding/project as BNodes with and without `prefLabel`; no `N[0-9a-f]{32}`-shaped ARC strings; two `map_graph` runs yield the same content-relevant funding fields.

### Non-goals

- Sharing a common helper with `GeneralSchemaOrgMapper` in this change (optional follow-up; Regal uses `skos:prefLabel`, Schema.org uses `schema:name`).
- Changing funding mapping semantics beyond blank-node safety (joined vs flat preference stays per `docs/regal_mapping.md`).
- API hasher / volatile-field handling (`datePublished` already stripped server-side).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `regal-to-arc-mapping`: Persisted Regal ARC string fields (including Funding Program / Project ID / Funder and other values from `_str`/`_strs`) MUST NOT embed rdflib blank-node labels; blank nodes without `skos:prefLabel` MUST be skipped.

## Impact

- `middleware/linked_data/.../regal_mapper.py` (`_str`, `_strs`, `_funding_values`, related callers).
- Unit tests in `middleware/linked_data/tests/unit/test_regal_mapper.py`.
- OpenSpec delta under `regal-to-arc-mapping` (extends the existing opaque-comment blank-node rule to mapper string helpers / funding).
- Production: fewer false `has_changes` pushes for Publisso on draven after deploy.
