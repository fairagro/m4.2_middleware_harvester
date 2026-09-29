# Tasks

## 1. PayloadKind + InspireRecord models in payload

- [ ] 1.1 Add `PayloadKind.inspire_record` to `middleware.payload.kinds` and verify existing kinds still resolve
- [ ] 1.2 Move `InspireRecord` and nested DTOs from `middleware.inspire.models` into `middleware.payload` (e.g.
      `payload/inspire/models.py`); update inspire IsoParser/CSW/tests imports; verify inspire unit imports and a model
      round-trip test pass; confirm import-linter `payload-isolation` still passes

## 2. inspire_general DataMapper

- [ ] 2.1 Add `MapperType.inspire_general` and implement/register `DataMapper` accepting `inspire_record` (move logic
      from `middleware.inspire.mapper`); `map(ParsedPayload, MappingContext)` yields `HarvestedArc`; verify existing
      mapper behaviour tests still pass after import path updates
- [ ] 2.2 Register builtins so harvester config validation and the inspire plugin resolve `inspire_general`; verify
      registry lookup and `accepts == inspire_record`
- [ ] 2.3 Remove or shim-delete the old inspire-local mapper module so the plugin cannot call a second implementation;
      verify no remaining `middleware.inspire.mapper` production imports (except optional deprecated re-export)

## 3. Plugin + orchestrator + config wiring

- [ ] 3.1 Change `InspirePlugin` to take `MapperConfig`, build `ParsedPayload` + `MappingContext` (http(s) `source_url`
      via `as_source_url` / CSW record URL), call shared `map`, yield all `HarvestedArc`s; verify plugin unit tests
      updated for the new constructor and mapping path
- [ ] 3.2 Update orchestrator `_create_plugin` so `inspire` receives `(config, mapper)` like `linked_data`; verify
      factory fails closed when mapper missing (guarded by config validation)
- [ ] 3.3 Require sibling `mapper` for inspire in `RepositoryConfig` and validate `accepts == inspire_record`; verify
      unit tests: missing mapper rejected; `inspire_general` accepted; wrong kind rejected
- [ ] 3.4 Update all in-repo inspire YAML examples (`dev_environment/`, etc.) with `mapper: { type: inspire_general }`
      and verify configs validate

## 4. Docs / principles overlay

- [ ] 4.1 Update `openspec/principles.md` module graph so inspire maps via payload (not `inspire/mapper.py` owning ARC
      mapping) and verify the narrative matches the principles delta
- [ ] 4.2 Touch AGENTS.md only if the documented package list needs `inspire_record` / `inspire_general`; verify docs
      paths still resolve

## 5. Integration check

- [ ] 5.1 Run inspire + payload + harvester config unit tests and verify green
- [ ] 5.2 Run `openspec validate --changes` for `inspire-mapper-to-payload` and verify the change validates
- [ ] 5.3 Confirm non-goals: IsoParser still in inspire; no shared ISO parser; no default mapper when omitted
