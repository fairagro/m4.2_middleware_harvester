# Tasks

## 1. Config hard-cut

- [x] 1.1 Remove `catalog_name` / `catalog_url` from `CkanextDcatMapperConfig`, `_MAPPER_TYPE_LOCAL_FIELDS`,
      `MapperConfig` properties, blank validators, and `_LEGACY_CATALOG_FIELDS_MSG` / `_warn_deprecated_catalog_fields`
      in `middleware/payload/.../mapper_config.py`
- [x] 1.2 Update unit tests that assert deprecation warnings or accept catalog fields (`test_data_mapper_registry.py`,
      related) so leftover keys fail closed

## 2. Mapper behaviour

- [x] 2.1 Remove `catalog_*` constructor args and `Comment("Data Catalog")` branch from `CkanextDcatMapper` /
      `_CkanextDcatRun`; update `test_ckanext_dcat_mapper.py`
- [x] 2.2 Rewrite `docs/mappers/ckanext-dcat.md` (NOTE, Identity / Investigation rows, Fallbacks, Refusal table) so
      catalog provenance is API `known_rdis` only

## 3. Verify

- [x] 3.1 `openspec validate --specs` (or change validate) and
      `uv run pytest middleware/payload/tests/unit/test_ckanext_dcat_mapper.py middleware/payload/tests/unit/test_data_mapper_registry.py -q`
