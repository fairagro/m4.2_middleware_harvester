# Proposal

## Why

INSPIRE CSW harvesting still owns both protocol I/O and `InspireRecord`→ARC mapping inside `middleware.inspire`. After
#140, vocabulary mappers belong in `middleware.payload` so the same mapper can serve ISO-derived records from other
transports later (e.g. OAI-PMH + ISO). Keeping a second ISO→ARC implementation would diverge from Schema.org / Regal /
OAI patterns (`mapper:` sibling + shared `DataMapper`).

## What Changes

- Add `PayloadKind.inspire_record` and move `InspireRecord` (+ nested DTOs) into `middleware.payload`
- Register `mapper.type: inspire_general` as a shared `DataMapper` accepting `inspire_record` (behaviour preserved from
  today’s `InspireMapper` / `docs/inspire_mapping.md`)
- **BREAKING:** `inspire` repositories MUST set sibling `mapper: { type: inspire_general }` (parity with `linked_data` /
  `generic` / `oai_pmh` mapper requirement; no silent default)
- Wire `InspirePlugin` + orchestrator like `linked_data`: `(plugin_config, mapper_config)` — CSW/`IsoParser` stay in
  `inspire` (no shared `parser:` yet)
- Update OpenSpec ownership (mapping in `payload`; plugin owns CSW) and example configs
- Non-goals: folding CSW into generic Protocol; moving `IsoParser` to `middleware.parsing`; PhenoRoam / non-ISO schemas

## Capabilities

### New Capabilities

- (none — behaviour already specified under `inspire-to-arc-mapping`; ownership moves)

### Modified Capabilities

- `payload`: add `inspire_record` kind; register `inspire_general` DataMapper; models live in payload
- `inspire-to-arc-mapping`: mapping implementation lives in `middleware.payload`; plugin consumes via registry
- `inspire-workflow-execution`: plugin maps via shared DataMapper + repository `mapper` config; yields `HarvestedArc`
- `harvester-configuration`: require `mapper` for `inspire` repositories; validate `inspire_general` / kind alignment
- `principles`: module graph — inspire plugin → payload mapper; models no longer owned solely by inspire

## Impact

- Packages: `middleware.payload`, `middleware.inspire`, `middleware.harvester` (config + orchestrator factory)
- Configs: all `inspire:` YAML examples / prod samples gain `mapper: { type: inspire_general }`
- Tests: mapper suite moves or re-imports from payload; plugin tests mock shared mapper
- Import-linter: payload remains isolated from inspire; inspire MAY import payload
- Follow-on (out of scope): OAI+ISO PayloadParser reusing `inspire_general`
