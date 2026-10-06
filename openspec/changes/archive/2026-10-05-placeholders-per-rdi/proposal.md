## Why

#413 (PR #432) added placeholder handling, but the list could only be set for INSPIRE
(`value_bounds.placeholder_values`), and the schema.org and Regal mappers used the fixed defaults. Different RDIs write
different placeholder strings, so the list has to be configurable per RDI, in one place for all plugins (review comment
on #432).

The review of #437 added three rules: defaults belong on the pydantic config model only, the placeholders travel as a
config object, and nothing is dropped unless the operator configured it (no built-in list, no implicit template
matching).

## What Changes

- New per-repository config object `mapper.placeholders` (`PlaceholderConfig` in `middleware.payload.placeholders`):
  `values` (folded: trimmed, case-insensitive) and `unrendered_templates` (`$var`, `${var}`, `{{var}}`). **Both default
  to empty/off**, so nothing counts as a placeholder unless configured. `DEFAULT_PLACEHOLDER_VALUES`, `is_placeholder`
  and `normalize_placeholder_values` are removed; `PlaceholderConfig.matches` replaces them.
- INSPIRE: `InspirePlugin` passes the `PlaceholderConfig` to `CSWClient` → `IsoParser`, which put it into the
  `InspireRecord` validation context under `PLACEHOLDERS_CONTEXT_KEY`. Both now require their config arguments
  (`IsoParser(value_bounds, placeholders)`); they no longer supply defaults. **`value_bounds.placeholder_values` is
  removed** (added in #432 and never released, so no deployed config uses it).
- Schema.org and Regal: `from_config` passes the `PlaceholderConfig` to the mapper; it applies to the `License` /
  `Language` / `Version` / `URL` Comments and to the ARC licence (`license_from_value(..., placeholders=...)`).
- Config: `config.all-rdis.yaml` sets the placeholders for BonaRes (`values`) and e!DAL (`unrendered_templates`); the
  Helm example shows the block.

## Capabilities

### Modified Capabilities

- `harvester-configuration`: `mapper.placeholders`.
- `inspire-to-arc-mapping`: the placeholders come from the repository mapper config.
- `schemaorg-to-arc-mapping`: the placeholders come from the repository mapper config.

## Impact

- **Behaviour change for unconfigured RDIs:** placeholders from #432 (`None`, `No information provided`, `$licenseURL`,
  …) are kept again until the repository lists them. Deployments must add `mapper.placeholders` for BonaRes, Thünen
  Atlas and e!DAL before rolling out, otherwise e.g. 44 BonaRes records with a `graphicOverview` "None" fail validation
  again.
