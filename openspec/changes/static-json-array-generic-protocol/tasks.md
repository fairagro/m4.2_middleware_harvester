# Tasks

## 1. Protocol

- [x] 1.1 Add `ProtocolType.static_json_array` and `StaticJsonArrayProtocol`
      (`middleware/generic/protocol/static_json_array.py`); register in `generic/plugin.py` and harvester config
      validation
- [x] 1.2 Unit tests: single GET, non-array / invalid JSON errors, non-object elements, shared-DOI records, identical
      record dedup, reorder stability, expected count (`generic/tests/unit/test_static_json_array_protocol.py`)

## 2. Discovery and plugin

- [x] 2.1 Optional `JsonLdDiscoveryResult.harvest_source_id` (`parsing/discovery.py`) + tests
      (`parsing/tests/unit/test_discovery.py`)
- [x] 2.2 `GenericPlugin._process_result` propagates it into `MappingContext`
- [x] 2.3 End-to-end `GenericPlugin.run()` test: shared-DOI records stay distinct ARCs

## 3. Parser

- [x] 3.1 Local Schema.org context in `JsonLdParser`; tests for string / list contexts without network, and rejection of
      other remote contexts next to Schema.org

## 4. Wiring and validation

- [x] 4.1 PlabiPD entry in `dev_environment/config.all-rdis.yaml` under `generic:`
- [ ] 4.2 Live harvest of `genomes.json` via `GenericPlugin`
- [x] 4.3 ruff, mypy, pylint, bandit, `uv run pytest middleware/`
