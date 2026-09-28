## 1. Value-bounds module

- [x] 1.1 New `middleware/inspire/src/middleware/inspire/value_bounds.py`: `MAX_STR_SHORT/MEDIUM/LONG`,
      `MAX_LIST_ITEMS`, `truncate`, `bounded_str`, `bounded_list`, `valid_http_url`
- [x] 1.2 `valid_http_url` rejects non-http(s) schemes, protocol-relative URLs, and oversized values; drops rather than
      raises

## 2. `iso_parser.py` — bound every extraction site

- [x] 2.1 Free-text fields (`title`, `abstract`, `identifier`, `lineage`, `supplemental_information`, `purpose`,
      `edition`, `alternate_title`, `status`, metadata-level fields, `Contact.name`/`organization`) truncated per tier
- [x] 2.2 Every unbounded list field capped at `MAX_LIST_ITEMS`, with per-element string truncation and loop-iteration
      capping at the source (`items[:MAX_LIST_ITEMS]`)
- [x] 2.3 Every URL field routed through `valid_http_url` (drop on failure); `OnlineResource.url` — the one non-optional
      URL field — drops the whole entry when invalid, not just the URL
- [x] 2.4 `_extract_resolution_denominators`'s `int()` guarded with `contextlib.suppress(ValueError, TypeError)` —
      malformed denominator dropped, not record-fatal

## 3. Identifier sanitization reuse

- [x] 3.1 New `middleware/payload/src/middleware/payload/identifier_sanitizer.py`: `sanitize_identifier`,
      `to_identifier_slug` (plain functions)
- [x] 3.2 `LinkedDataMapper.sanitize_identifier`/`.to_identifier_slug` become thin delegating wrappers; unused `re`
      import removed
- [x] 3.3 `middleware/inspire/src/middleware/inspire/mapper.py`: private `_to_identifier_slug` removed; imports the
      shared functions; all 4 call sites keep `"untitled"` fallback parity (`to_identifier_slug(...) or "untitled"`)
- [x] 3.4 `map_investigation` sanitizes every identifier (URL-shaped and raw), not only URL-shaped ones

## 4. Config-level bounds

- [x] 4.1 `Config.csw_url` gains an http(s)-only `field_validator` (raises on invalid)
- [x] 4.2 `Config.max_records` gains `ge=1, le=1_000_000`; `None` (unbounded) untouched

## 5. Tests

- [x] 5.1 New `middleware/inspire/tests/unit/test_value_bounds.py`
- [x] 5.2 New `middleware/inspire/tests/unit/test_iso_parser.py`: oversized title/ abstract truncated; oversized list
      capped; bad-scheme URL dropped, good one kept; bad-scheme `OnlineResource.url` drops the whole entry; **key
      regression** — malformed denominator dropped, record still parses; `dataset_uri` scheme check
- [x] 5.3 `test_mapper_comprehensive.py`: `test_to_identifier_slug` updated for the extracted function (empty title →
      `None`, not `"untitled"`); new `test_map_study_falls_back_to_untitled_when_title_empty`,
      `test_map_assay_falls_back_to_untitled_when_title_empty`,
      `test_map_investigation_sanitizes_raw_non_url_identifier`
- [x] 5.4 New `middleware/inspire/tests/unit/test_inspire_config.py` (named to avoid a module-basename collision with
      `middleware/linked_data/tests/unit/test_config.py` under the shared root `pythonpath`): `csw_url` scheme
      rejection/acceptance, `max_records` ceiling rejection/acceptance, `max_records=None` stays unbounded
- [x] 5.5 New `middleware/payload/tests/unit/test_identifier_sanitizer.py`
- [x] 5.6 Existing `middleware/payload/tests/unit/test_regal_mapper.py` (already exercises `sanitize_identifier` via
      `RegalMapper`) passes unmodified against the delegating wrapper

## 6. Validation

- [x] 6.1 `uv run pytest -m "not integration and not system_local and not system_external"` green — full repo: 520
      passed
- [x] 6.2 `bash scripts/run-quality-cli.sh mypy --config-file mypy.ini middleware/` clean
- [x] 6.3 `uv run ruff check` / `uv run ruff format --check` clean for touched files (two pre-existing, untouched
      `no-self-use` findings elsewhere in the tree, unrelated to this change)
- [x] 6.4 `bash scripts/run-quality-cli.sh pylint --rcfile .pylintrc middleware/` — 9.96/10, only the pre-existing known
      local-only `E0401` test-helper import noise
- [x] 6.5
      `bash scripts/run-quality-cli.sh bandit -c pyproject.toml -r     middleware/inspire/src middleware/payload/src`
      clean (one pre-existing, unrelated low-severity finding at `csw_client.py:986`, not touched by this change)
- [x] 6.6 `openspec validate 2026-09-28-bound-inspire-harvested-values --strict`
- [x] 6.7 `npx prettier --check` on all new `.md` files before pushing
