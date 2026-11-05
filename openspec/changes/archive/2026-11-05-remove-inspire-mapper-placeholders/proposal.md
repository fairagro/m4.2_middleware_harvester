# Proposal

## Why

#476 soft-deprecates `mapper.placeholders` on `inspire` repositories (lift + warning into `inspire.placeholders`). Infra
overlays on fizz/draven already migrated (#54 / #55). Soft-lift is leftover migration debt: operators can still ship the
old location, and OpenSpec still requires accepting it.

## What Changes

- **BREAKING:** Delete `RepositoryConfig.lift_inspire_mapper_placeholders` and
  `_LEGACY_INSPIRE_MAPPER_PLACEHOLDERS_MSG`. Do **not** replace them with a dedicated reject/migration validator for
  leftover `mapper.placeholders` on inspire (“raus ist raus”).
- INSPIRE continues to read placeholders only from `inspire.placeholders`. `mapper.placeholders` remains a normal
  `MapperConfig` field for `generic` / `oai_pmh` (linked-data mappers).
- Update OpenSpec (`harvester-configuration`: remove the deprecation/lift requirement), `docs/mappers/inspire.md`, and
  unit tests.
- **BREAKING** note via Conventional Commit (`feat!:` / `BREAKING CHANGE:`) so Release changelog surfaces it.

**Non-goals:** Soft-default when an `inspire` repository omits `mapper` entirely. Removing `mapper.placeholders` for
non-inspire plugins. Dedicated “use inspire.placeholders” error copy for leftover `mapper.placeholders` on inspire.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-configuration`: Drop the requirement that `mapper.placeholders` on inspire soft-lifts; keep per-plugin
  placeholder location (`inspire.placeholders` vs `mapper.placeholders` for generic/oai_pmh).

## Impact

- `middleware/harvester` `RepositoryConfig` + unit tests
- `docs/mappers/inspire.md` deprecation wording
- OpenSpec delta above
- Follow-up: close #477 on merge
