# Proposal

## Why

`MapperConfig.catalog_name` / `catalog_url` (added in #359) let repository YAML stamp an Investigation
`Comment("Data Catalog")` from the `ckanext_dcat` mapper. They are DCAT-AP-only settings on the shared `MapperConfig`,
and the middleware API now adds the same provenance for every client from its `known_rdis` registry (`RDI` /
`RDI Description` / `RDI URL`, fairagro/m4.2_advanced_middleware_api#560). Keeping both lets harvester YAML and
`known_rdis` drift apart. A deployed config still sets the fields, so they are soft-deprecated first (#461) and removed
in a follow-up.

## What Changes

- Emit a `logger.warning` at config load when a `mapper:` block sets `catalog_name` or `catalog_url` (blank values stay
  unset and do not warn). Mapper behaviour unchanged: `CkanextDcatMapper` still writes `Comment("Data Catalog")`.
- Mark both fields as deprecated in their descriptions and in `docs/mappers/ckanext-dcat.md`.
- Drop the keys from the in-repo SRADI example (`dev_environment/config.all-rdis.yaml`).
- **Non-goals:** Removing the fields or the `Data Catalog` comment (**BREAKING** — #471). Out-of-repo deployment configs
  (fairagro/m4.2_infrastructure). API `known_rdis` content.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `ckanext-dcat-to-arc-mapping`: Catalog provenance config is deprecated and warns at config load.

## Impact

- `middleware/payload` `MapperConfig` validator + unit tests
- `docs/mappers/ckanext-dcat.md`, `dev_environment/config.all-rdis.yaml`
- Follow-up hard removal (#471) after SRADI's `known_rdis` entry has `description` / `url` and deployed configs drop the
  keys
