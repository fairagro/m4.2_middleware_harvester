## 1. Hardened parser

- [x] 1.1 New `middleware/inspire/src/middleware/inspire/xml_hardening.py` exporting `HARDENED_XML_PARSER`, built
      with `resolve_entities=False`, `no_network=True`, `load_dtd=False`, `huge_tree=False`, `remove_comments=True`
- [x] 1.2 That module imports `owslib.etree` itself, then calls `lxml.etree.set_default_parser(...)`, so the
      ordering guarantee holds regardless of import order elsewhere
- [x] 1.3 Pass it explicitly as `parser=` to the `lxml.etree.fromstring` call in `_prepare_xml_paging`

## 2. Regression tests

- [x] 2.1 New `middleware/inspire/tests/unit/test_xml_hardening.py`
- [x] 2.2 Internal entity declaration is not expanded (main thread)
- [x] 2.3 External `SYSTEM` entity never yields file contents (main thread) — accept `XMLSyntaxError` or empty
      text, assert the content is absent
- [x] 2.4 Both of the above hold on a `ThreadPoolExecutor` worker
- [x] 2.5 Explicit-parser path: hostile `xml_query` cannot expand entities, and a malformed one still raises
      `ValueError`
- [x] 2.6 Comment/namespace behaviour is unchanged for a realistic ISO 19139 snippet

## 3. Validation

- [x] 3.1 `uv run pytest -m "not system_local and not system_external"` green
- [x] 3.2 `uv run mypy` with `MYPYPATH` from `.devcontainer/product.env` clean
- [x] 3.3 `uv run ruff check` / `ruff format --check` clean; bandit and pylint pass
- [x] 3.4 `openspec validate harden-csw-xml-parsing` passes
