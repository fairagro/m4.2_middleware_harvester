## Why

#413 (PR #432) added placeholder handling, but the list could only be set for INSPIRE
(`value_bounds.placeholder_values`), and the schema.org and Regal mappers used the fixed defaults. Different RDIs write
different placeholder strings, so the list has to be configurable per RDI, in one place for all plugins (review comment
on #432).

## What Changes

- New per-repository field `mapper.placeholder_values` (`MapperConfig`, default `DEFAULT_PLACEHOLDER_VALUES`). Setting
  it replaces the defaults; values are folded (trimmed, case-insensitive). Unrendered `$var` / `{{var}}` templates
  always count.
- INSPIRE: `InspirePlugin` passes the list to `CSWClient` → `IsoParser`, which puts it into the `InspireRecord`
  validation context under `PLACEHOLDER_VALUES_CONTEXT_KEY`. **`value_bounds.placeholder_values` is removed** (added in
  #432 and never released, so no deployed config uses it).
- Schema.org and Regal: `from_config` passes the list to the mapper; it applies to the `License` / `Language` /
  `Version` / `URL` Comments and to the ARC licence (`license_from_value(..., placeholder_values=...)`).

## Capabilities

### Modified Capabilities

- `harvester-configuration`: `mapper.placeholder_values`.
- `inspire-to-arc-mapping`: the list comes from the repository mapper config.
- `schemaorg-to-arc-mapping`: the list comes from the repository mapper config.

## Impact

- No behaviour change with the defaults. Operators can now set the list per RDI in the `mapper` block.
