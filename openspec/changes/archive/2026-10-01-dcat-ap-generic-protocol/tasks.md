# Tasks

## 1. Protocol

- [x] 1.1 Add `ProtocolType.dcat_ap` and `DcatApProtocol` (`middleware/generic/protocol/dcat_ap.py`): Hydra pagination,
      loop detection, per-dataset subgraph → `JsonLdDiscoveryResult`, `hydra:totalItems` expected count; register in
      `generic/plugin.py` and harvester config validation
- [x] 1.2 Unit tests: pagination, subgraph contents, expected count, loop error, invalid page error, no `@context` in
      payload (`generic/tests/unit/test_dcat_ap_protocol.py`)

## 2. Parser

- [x] 2.1 Add `ParserType.jsonld` and `JsonLdParser` (`middleware/parsing/parser/jsonld.py`); register in
      `register_builtin_parsers`
- [x] 2.2 Unit tests: registry, happy path, thread offload, wrong discovery type, empty payload / graph, remote context
      rejection, inline context accepted (`parsing/tests/unit/test_jsonld_parser.py`)

## 3. Mapper

- [x] 3.1 Add `MapperType.ckanext_dcat` / `CkanextDcatMapper` plus `MapperConfig.catalog_name` / `catalog_url`
- [x] 3.2 Unit tests (`payload/tests/unit/test_ckanext_dcat_mapper.py`)

## 4. Wiring and validation

- [x] 4.1 SRADI entry in `dev_environment/config.all-rdis.yaml` under `generic:`; validated with `RepositoryConfig`
- [x] 4.2 End-to-end `GenericPlugin.run()` unit test with mocked HTTP catalog
- [x] 4.3 Live harvest of `https://agrihub.gis.lrg.tum.de/catalog.jsonld` via `GenericPlugin`: 351/351, 0 errors
- [x] 4.4 `uv run ruff format --check`, `ruff check`, mypy, pylint, bandit, `uv run pytest middleware/`
