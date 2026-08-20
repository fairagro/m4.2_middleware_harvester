## Why

Publisso/Regal harvests emit a new unstable Investigation Comment on nearly every run because `RegalMapper._add_opaque_comments` falls back to `str(obj)` for blank-node objects without `skos:prefLabel`. Those strings are rdflib parser labels (`N` + 32 hex / `_:…`) that change on every JSON-LD parse, so the Advanced Middleware sees a content change, recomputes hashes, and pushes a new Git commit even when the dataset is unchanged. `contributorOrder` is the known trigger today (not in `_KNOWN_PREDICATES`, documented as contact-ordering metadata in `docs/regal_mapping.md`), but any unknown predicate with an unlabelled blank node has the same failure mode.

## What Changes

- Treat `regal:contributorOrder` as a known predicate so it is not emitted as an opaque Comment.
- Never persist rdflib blank-node labels into ARC Comments (or analogous label paths): skip blank nodes without a stable `skos:prefLabel` / URIRef; keep Literals, URIRefs, and labelled nodes.
- Add unit tests that prove `contributorOrder` and other unlabelled blank-node opaque predicates produce harvest-stable Comment sets.
- Optionally (only if order keys are stable Literals/URIRefs with low effort): use `contributorOrder` to sort Creator/Contributor contacts; otherwise leave a TODO / follow-up and keep skip-only behavior.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `regal-to-arc-mapping`: Regal opaque Comments and labelled-node helpers MUST NOT embed blank-node labels; `contributorOrder` MUST NOT become an Investigation Comment.

## Impact

- Code: `middleware/linked_data/src/middleware/linked_data/linked_data_mapper/regal_mapper.py`
- Tests: `middleware/linked_data/tests/unit/test_regal_mapper.py`
- Docs already state intent (`docs/regal_mapping.md`); no API, Schema.org, DataHUB CI, or hash-workaround changes.
- Non-goals: `m4.2_advanced_middleware_api`, Schema.org keywords, DataHUB CI, API content-hash ignore lists.
