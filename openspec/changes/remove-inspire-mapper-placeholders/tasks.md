# Tasks

## 1. Harvester config

- [ ] 1.1 Delete `RepositoryConfig.lift_inspire_mapper_placeholders` and `_LEGACY_INSPIRE_MAPPER_PLACEHOLDERS_MSG` (no
      reject replacement); verify focused harvester config tests fail until updated —
      `uv run pytest middleware/harvester/tests/unit/test_config.py -q -k placeholders`
- [ ] 1.2 Update unit tests: `inspire.placeholders` still loads; lift / conflict / warn scenarios removed or rewritten
      so leftover `mapper.placeholders` on inspire does not lift; generic `mapper.placeholders` unchanged — verify
      `uv run pytest middleware/harvester/tests/unit/test_config.py -q -k placeholders` green

## 2. Docs + gate

- [ ] 2.1 Scrub `docs/mappers/inspire.md` deprecation/lift wording for `mapper.placeholders`; verify no “lifted with a
      warning” claim remains
- [ ] 2.2 Run `openspec validate remove-inspire-mapper-placeholders` and focused pytest; verify green
