# Tasks

## 1. MapperConfig type-as-key + soft lift

- [x] 1.1 Redesign `MapperConfig` for type-as-key children + shared `placeholders`; lift deprecated `{ type: … }` with
      `logger.warning`; keep a stable active-type accessor for plugins — verify unit tests for nested load, legacy lift,
      dual-type reject
- [x] 1.2 Update harvester / plugin call sites that read `mapper.type` or type-local fields to use the new accessors —
      verify existing harvester config tests still pass (with warning expectations where legacy)

## 2. ParserConfig type-as-key + soft lift

- [x] 2.1 Redesign `ParserConfig` for type-as-key children; move `allowed_context_url` / `jsonld_parse_threshold_bytes`
      under JSON-LD type children; lift deprecated `{ type: … }` with warning — verify unit tests for nested / legacy /
      dual-type
- [x] 2.2 Update generic / oai_pmh / parsing call sites that read `parser.type` or parser fields — verify focused pytest
      for generic + oai_pmh + parsing config

## 3. Operator-facing examples and OpenSpec wording polish

- [x] 3.1 Flip in-repo YAML/Helm examples (`dev_environment/`, `helm/harvester/values.yaml`) to nested mapper/parser;
      note linked_data type-as-key non-goal in `docs/linked_data_to_generic.md` if needed — verify configs still
      validate
- [x] 3.2 Confirm OpenSpec deltas match shipped behaviour; run `openspec validate` for the change

## 4. Hard-cut follow-up

- [x] 4.1 Ensure GitHub follow-up Task exists to remove legacy `mapper.type` / `parser.type` after the migration window
      (`relation: sub-of #384`) — https://github.com/fairagro/m4.2_middleware_harvester/issues/478
