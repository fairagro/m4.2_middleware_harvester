# Proposal

## Why

#459 (option B, agreed with @Zalfsten): placeholders stay operator-configurable, but INSPIRE reads them from the wrong
block. The INSPIRE check runs in the parser, yet `InspirePlugin` takes `mapper.placeholders` out of `MapperConfig` and
hands it to `CSWClient` / `IsoParser` as a second constructor argument. That couples the plugin to the mapper config
(see #473) and breaks the "one config object per functional class" rule. The linked-data mappers each keep their own
copy of the same `placeholders` plumbing.

## What Changes

- INSPIRE plugin `Config` gains `placeholders` (`PlaceholderConfig`), next to `value_bounds`. Both live on a new
  `IsoParserConfig` base, so `IsoParser` and `CSWClient` take a single config object. The YAML stays flat
  (`inspire.placeholders`, `inspire.value_bounds`).
- `middleware.payload.inspire.models` exposes `validation_context(value_bounds, placeholders)`; the context-key
  constants become private.
- `InspirePlugin` no longer reads `mapper_config.placeholders`.
- **Deprecation:** an `inspire` repository that sets `mapper.placeholders` validates with a `logger.warning`, and the
  value is lifted to `inspire.placeholders`. Setting both to different values fails validation. Deployed `bonares` and
  `thunen_atlas` use the old location (m4.2_infrastructure `fizz` / `draven`). Removal follows in a separate issue.
- `LinkedDataMapper` owns `placeholders` (constructor, property, `license()` helper over `license_from_value`);
  `GeneralSchemaOrgMapper`, `RegalMapper` and `CkanextDcatMapper` use the base instead of their own copies.
- Mapper docs state the placeholder contract per mapper, so a future Markdown→mapper generator emits the check.
- **Non-goals:** plugin/mapper decoupling (orchestrator builds the mapper, #473); removing `mapper.placeholders` for
  `inspire` (follow-up issue); changing which values count as placeholders; migrating out-of-repo deployment config.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-configuration`: placeholders location per plugin; deprecation of `mapper.placeholders` on `inspire`.
- `inspire-to-arc-mapping`: parser reads placeholders from `IsoParserConfig`; `validation_context()` replaces public
  context keys.
- `linked-data-mapper`: `LinkedDataMapper` holds the repository placeholders.
- `mapper-docs`: each mapper document states its placeholder contract.

## Impact

- `middleware/inspire` (`config.py`, `iso_parser.py`, `csw_client.py`, `plugin.py`) and tests
- `middleware/payload` (`inspire/models.py`, `linked_data_mapper/*`) and tests
- `middleware/harvester` `RepositoryConfig` validator and tests
- `docs/mappers/{README,inspire,schemaorg,regal}.md`, `helm/harvester/values.yaml`, `dev_environment` examples
