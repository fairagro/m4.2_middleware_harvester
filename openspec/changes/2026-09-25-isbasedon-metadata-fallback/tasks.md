## 1. Fallback-subject chain (StableGraph)

- [ ] 1.1 `ResourceView` accepts an optional ordered fallback-subject chain; `ResourceView.with_fallback(*subjects)`
      returns a new view, `__init__` keeps its plain two-argument form
- [ ] 1.2 `_all_objects` retries against each fallback subject in order when the primary subject yields no objects;
      first non-empty result wins, results are never merged
- [ ] 1.3 `node`, `iri` and `is_type` ignore the chain; views returned by `resources()` / `_label_for` are plain
- [ ] 1.4 `schema_dois` / `dois_from` fall back on no *parsed DOI*, not merely on no objects
- [ ] 1.5 Chain is one hop — a fallback subject's own chain is not consulted

## 2. isBasedOn bridge (Schema.org mapper)

- [ ] 2.1 `_SchemaOrgRun.view()` builds the Dataset's view with its `schema:isBasedOn` targets as the chain, ordered by
      `stable.sort_key`
- [ ] 2.2 Record each property resolved through the chain as an Investigation Comment naming the property and
      `isBasedOn`, mirroring `_add_title_fallback_comment`
- [ ] 2.3 Title resolution is left on the Dataset subject only — `_resolve_dataset_title` must not see the chain
- [ ] 2.4 Confirm `_plan_investigation_identifier` still resolves from the Dataset's own IRI (no code change expected;
      assert it in a test)

## 3. Unit tests

- [ ] 3.1 Thin Dataset recovers description, contacts, url and publication DOI from a `ScholarlyArticle` `isBasedOn`
- [ ] 3.2 Dataset's own description / single creator survive; the target's twelve authors are not appended
- [ ] 3.3 Placeholder `schema:name` is kept; title never comes from `isBasedOn`
- [ ] 3.4 Occupied `schema:identifier` carrying no DOI still falls back to the target's DOI
- [ ] 3.5 Two Datasets sharing one `isBasedOn` target get distinct identifiers and neither is the target's DOI
- [ ] 3.6 Identity accessors and views reached via `resources()` ignore the chain
- [ ] 3.7 Multiple `isBasedOn` targets resolve in `sort_key` order across two different triple insertion orders
- [ ] 3.8 **Regression**: an existing fixture with no `isBasedOn` maps byte-identically to its pre-change ARC

## 4. Documentation

- [ ] 4.1 `docs/schemaorg_mapping.md` records the `isBasedOn` recovery rule and its Comment
- [ ] 4.2 This proposal's spec deltas merged into `openspec/specs/stable-graph/` and
      `openspec/specs/schemaorg-to-arc-mapping/`

## 5. Validation

- [ ] 5.1 `uv run ruff format --check --config ruff.toml middleware/payload` /
      `uv run ruff check --config ruff.toml middleware/payload`
- [ ] 5.2 `source product.env` then `uv run mypy middleware/` (src **and** tests)
- [ ] 5.3 `uv run pylint middleware/payload/src/ middleware/payload/tests/unit/`
- [ ] 5.4 `uv run pytest middleware/payload/tests/unit middleware/linked_data/tests/unit -q`
- [ ] 5.5 Verify in the container **and** from source, diffing the ARC payloads from both runs
- [ ] 5.6 `openspec validate 2026-09-25-isbasedon-metadata-fallback`
