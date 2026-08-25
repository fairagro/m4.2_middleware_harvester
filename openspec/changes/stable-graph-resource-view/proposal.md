## Why

Linked-data mappers repeatedly leak rdflib blank-node labels and unstable
iteration order into ARC fields (`str(BNode)`, `graph.value`, unsorted
`graph.objects`). Schema.org already carries a large private hygiene layer;
Regal still has weaker helpers. Without a shared hard access API, every new
vocabulary mapper will rediscover the same harvest-stability bugs.

## What Changes

- Introduce a **StableGraph / ResourceView** RDF access layer
  (`stable_graph.py`) so vocabulary mappers never use raw rdflib nodes as
  string sources for ARC text.
- Centralize access determinism: language preference, multi-value dedupe/sort,
  BNode content signatures (never BNode labels), separate literal vs resource
  accessors, `doi()` (including Schema.org `PropertyValue`), `http_iri()`,
  `labelled()`, optional `unknown_texts` / path helpers as needed for Schema.org.
- **BREAKING** (mapper ABC): replace `map_graph(..., source_url=, harvest_source_id=)`
  with `map_graph(graph, context: MappingContext)` (required; empty `MappingContext()`
  when no discovery data).
- Migrate **GeneralSchemaOrgMapper** onto ResourceView (behaviour-preserving
  vs existing unit tests); delete private RDF-hygiene helpers that the API
  absorbs.
- Plugin builds `MappingContext` from discovery and passes it to `map_graph`.
- Add API unit tests plus a shared `assert_harvest_has_no_bnode_labels` test helper.
- **RegalMapper** only updates the `map_graph` signature (ignore context); full
  Regal migration is a follow-up.

### Non-Goals

- YAML/JSON mapping DSL
- Graph skolemization
- Runtime hard-fail linter on every harvest
- Regal opaque/labelled migration onto ResourceView (follow-up)
- Moving Schema.org identifier cascade or publisher-invert policy into the API
- Import-lint forbidding `BNode` in mapper modules (optional later)

## Capabilities

### New Capabilities

- `stable-graph`: Hard RDF access API (`StableGraph` / `ResourceView` /
  `StableText`) with blank-node hygiene, language/multi-value policy,
  deterministic default iteration and singular picks, and helpers
  (`doi`, `http_iri`, `labelled`, …). No harvest/discovery context in wrap.

### Modified Capabilities

- `linked-data-mapper`: `map_graph` takes `MappingContext`; Schema.org mapper
  MUST use ResourceView for graph access; identifier cascade and publisher
  Comment policy remain mapper-local (composed from API bricks + context).
- `linked-data-harvesting`: Plugin MUST construct `MappingContext` from
  discovery (`source_url`, `harvest_source_id`) and pass it to `map_graph`.

## Impact

- **Affected domains**: new `openspec/specs/stable-graph/`; deltas on
  `linked-data-mapper`, `linked-data-harvesting`.
- **Code**: `middleware/linked_data/.../linked_data_mapper/` (`stable_graph.py`,
  ABC, `GeneralSchemaOrgMapper`, thin `RegalMapper` signature); plugin;
  unit tests under `middleware/linked_data/tests/unit/`.
- **Related**: GitHub issue
  [fairagro/m4.2_middleware_harvester#138](https://github.com/fairagro/m4.2_middleware_harvester/issues/138).
- **Dependencies**: none new (rdflib already in use).
- **Follow-up**: migrate `RegalMapper` onto the same API.
