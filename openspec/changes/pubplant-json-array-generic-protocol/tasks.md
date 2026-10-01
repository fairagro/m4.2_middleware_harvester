# Tasks

## 1. Protocol

- [x] 1.1 Add `ProtocolType.pubplant_json_array` and `PubPlantJsonArrayProtocol`
      (`middleware/generic/protocol/pubplant_json_array.py`); register in `generic/plugin.py` and harvester config
      validation
- [x] 1.2 Unit tests: single GET, non-array / invalid JSON errors, non-object elements, shared-DOI records, identical
      record dedup, reorder stability, no-fetch expected count
      (`generic/tests/unit/test_pubplant_json_array_protocol.py`)

- [x] 1.3 Extract `JsonArrayProtocol` base (`middleware/generic/protocol/json_array.py`); `PubPlantJsonArrayProtocol`
      builds on it
- [x] 1.4 Port `regal_find` as `RegalFindProtocol` (`ProtocolType.regal_find`) on the base; register in
      `generic/plugin.py` and harvester config validation
- [x] 1.5 `linked_data` `RegalFindSitemap` becomes a shim over `RegalFindProtocol`; existing Regal tests unchanged and
      green
- [x] 1.6 Unit tests (`generic/tests/unit/test_regal_find_protocol.py`, `test_protocol_registry.py`)

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
