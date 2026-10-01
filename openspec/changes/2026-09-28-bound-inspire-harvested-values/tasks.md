## 1. Configuration

- [x] 1.1 `ValueBounds` model in `middleware/payload/src/middleware/payload/inspire/value_bounds.py`
      (`max_str_short/medium/long`, `max_list_items`, `allowed_url_schemes`), exposed as `Config.value_bounds` with
      defaults
- [x] 1.2 `Config.csw_url` http(s)-only validator (hardcoded: functional OWSLib constraint)
- [x] 1.3 `Config.max_records`: arbitrary `le=1_000_000` ceiling removed (`ge=1` kept)

## 2. Model validation (`models.py`)

- [x] 2.1 Context-aware annotated types: `ShortStr`/`MediumStr`/`LongStr`, required variants, `HarvestedUrl`,
      `OptionalUrl` (blank → absent), `OptionalUri` (URL or URN, `dataset_uri`), `MaxItems` (before-validator)
- [x] 2.2 Codelist `Literal`s (MD_CharacterSetCode, MD_ScopeCode, MD_ProgressCode, CI_RoleCode, CI_DateTypeCode,
      MD_TopicCategoryCode, incl. ISO 19115-1), ISO 639-2 `LanguageCode`, ISO 8601 `IsoDate`, loose `Email`,
      `gco:Boolean` degree
- [x] 2.3 Applied to every field of `InspireRecord` and nested models

## 3. Parser (`iso_parser.py`)

- [x] 3.1 Truncate/drop layer and `value_bounds.py` removed; extractors return raw values, nested entries as dicts
- [x] 3.2 `IsoParser(value_bounds)` validates via `InspireRecord.model_validate(..., context=...)`; `CSWClient` passes
      `config.value_bounds`
- [x] 3.3 Denominators passed raw, validated as `list[int]`
- [x] 3.4 Distances passed raw, validated by `SpatialResolutionDistance` (review follow-up); `IsoDate` caps fractional
      seconds at 9 digits; `spatial_extent` fixed at 4 values

## 4. Identifiers

- [x] 4.1 `InspireMapper` imports `sanitize_identifier`/`to_identifier_slug` from the existing
      `middleware/payload/src/middleware/payload/identifiers.py` module; `LinkedDataMapper` already delegates
- [x] 4.2 `InspireMapper` uses the shared functions; `map_investigation` sanitizes every identifier and raises
      `ValueError` when empty
- [x] 4.3 `"untitled"` removed: study/assay/output-URI use title slug → sanitized `fileIdentifier` → `ValueError`

## 5. Tests

- [x] 5.1 `test_iso_parser.py`: rejection (not truncation) of oversized identifier/title/abstract/list; configured
      bounds incl. nested models; URL schemes (dangerous rejected, ftp accepted, blank absent, URN dataset URI);
      codelist and format violations; denominators; error message size
- [x] 5.2 `test_inspire_config.py`: `csw_url` scheme, no `max_records` ceiling, `value_bounds` defaults/override/invalid
- [x] 5.3 `test_mapper_comprehensive.py`: fileIdentifier fallback and `ValueError` instead of `"untitled"`; fixtures use
      valid codelist values
- [x] 5.4 `test_identifiers.py`; integration fixtures use real-world `ger`/`utf8`

## 6. Validation

- [x] 6.1 Live survey: 1,500 GDI-DE records + ZALF repository parsed with the new model — 3 new rejections (0.2%), all
      junk `dataSetURI`
- [x] 6.2 `uv run pytest middleware/` green (except the pre-existing, macOS-only
      `test_external_entities_do_not_leak_file_contents`, which needs `/etc/hostname`)
- [x] 6.3 ruff format/check, mypy, pylint (10.00/10), bandit clean
- [x] 6.4 `openspec validate 2026-09-28-bound-inspire-harvested-values --strict`
