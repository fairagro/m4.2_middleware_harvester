## 1. DOI extraction and identifier chain (mapper)

- [ ] 1.1 Add `_extract_all_dois(graph, subject) -> list[str]` and `_pick_canonical_doi(dois) -> str | None` (lexicographic `casefold` minimum)
- [ ] 1.2 Add `_extract_openagrar_mods_id(source_url) -> str | None` for `/receive/openagrar_mods_*` URLs
- [ ] 1.3 Implement `_resolve_investigation_identifier` decision chain with optional `colliding_dois: frozenset[str] | None` per design
- [ ] 1.4 Emit `Alternate Identifier` Comments for non-canonical DOIs on the same page; keep shared DOI in Publication/metadata when RDI ID is primary
- [ ] 1.5 Extend `LinkedDataMapper.map_graph` signature with optional `colliding_dois` (default `None`); `RegalMapper` ignores it

## 2. Per-run collision registry (plugin)

- [ ] 2.1 For Schema.org payload type, collect `(source_url, dois)` after graph fetch before final map (collect-then-map within plugin batch)
- [ ] 2.2 Build `colliding_dois = {doi | len(source_urls) > 1}` deterministically
- [ ] 2.3 Pass `colliding_dois` into each `map_graph` call for that harvest run
- [ ] 2.4 Preserve concurrent graph fetching where possible; only defer identifier-final mapping until collision set is known

## 3. Unit tests

- [ ] 3.1 Multi-DOI fixture (`00107508`-style): permuted identifier order → always `10.3220/253-2025-54`; alternate DOI in Comment
- [ ] 3.2 Two graphs, same PANGAEA DOI, different `openagrar_mods_*` URLs + `colliding_dois` → distinct RDI identifiers, DOI not primary
- [ ] 3.3 Single DOI regression: identifier unchanged; no spurious `Alternate Identifier`
- [ ] 3.4 Collision without extractable RDI ID: falls back to canonical DOI or URL logic per design
- [ ] 3.5 Sorcering pair (`00100605` / `00108456` style): both uniquely identifiable when applicable

## 4. Documentation

- [ ] 4.1 Add Key Decision to [`openspec/specs/linked-data-mapper/design.md`](openspec/specs/linked-data-mapper/design.md) documenting collision vs multi-DOI rules (during archive)

## 5. Validation

- [ ] 5.1 `uv run ruff format middleware/linked_data/`
- [ ] 5.2 `uv run pytest middleware/linked_data/tests/unit/test_mapper.py middleware/linked_data/tests/unit/test_linked_data_plugin.py -v`
