# Proposal

## Why

#461 deprecated `MapperConfig.catalog_name` / `catalog_url` (warn at config load; catalog provenance belongs to the
middleware API `known_rdis` registry). Infra overlays for fizz/draven no longer set those keys (#50 / #51 closed). Hard
removal (#471) can proceed so operators cannot reintroduce dead config and the DCAT mapper stops emitting
`Comment("Data Catalog")`.

## What Changes

- **BREAKING:** Remove `catalog_name` / `catalog_url` from `CkanextDcatMapperConfig` / `MapperConfig` (fields,
  blank-as-none validators, deprecation warning). Unknown leftover keys fail via existing type-child `extra="forbid"`.
- **BREAKING:** `CkanextDcatMapper` no longer accepts `catalog_*` constructor args and MUST NOT write
  `Investigation.Comment("Data Catalog")`.
- Update `docs/mappers/ckanext-dcat.md` and unit tests to match.
- OpenSpec delta for `ckanext-dcat-to-arc-mapping` reflecting the removal.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `ckanext-dcat-to-arc-mapping`: Drop optional catalog config and Data Catalog Investigation comment from the DataMapper
  / Investigation mapping contract.

## Impact

- Code: `middleware/payload` (`mapper_config.py`, `linked_data_mapper/ckanext_dcat_mapper.py`, unit tests)
- Docs: `docs/mappers/ckanext-dcat.md`
- Specs: `openspec/specs/ckanext-dcat-to-arc-mapping/`
- Operators: any remaining `mapper.ckanext_dcat.catalog_*` (or flat legacy lifts) MUST be removed before upgrade; RDI
  catalog comments come only from API `known_rdis`
