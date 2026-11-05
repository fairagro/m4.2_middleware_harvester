# Proposal

## Why

#384 soft-deprecates repository `mapper: { type: … }` / `parser: { type: … }` in favour of type-as-key nested children.
Infra overlays on fizz/draven already migrated (#52 / #53), and in-repo YAML uses nested form only. Soft-lift + warning
is leftover migration debt: operators can still ship the old discriminator, and OpenSpec still requires accepting it.

## What Changes

- **BREAKING:** Reject leftover `mapper.type` / `parser.type` discriminators at config validation with a clear pointer
  to type-as-key (e.g. `mapper: { schema_org_general: {} }`). Do **not** ignore `type:` as an unknown field.
- **BREAKING:** Delete soft-lift validators and deprecation warning messages for those discriminators (including flat
  type-local field lift that existed only for the legacy shape).
- Update OpenSpec (`harvester-configuration`, `payload`, `payload-parser`) and unit tests so nested form is the only
  accepted shape.
- Confirm in-repo YAML already uses nested form only (no migration edits expected).
- **BREAKING** note for operators via Conventional Commit (`feat!:` / `BREAKING CHANGE:`) so Release changelog surfaces
  it.

**Non-goals:** Soft-default when an `inspire` repository omits `mapper` entirely (separate deprecation). Changing
type-as-key registries, shared sibling fields (`placeholders`, JSON-LD settings under the type child), or the Python
`.type` property that reports the active registry key. Auto-migrating private out-of-repo YAML beyond closed infra
issues.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvester-configuration`: Require type-as-key only for `mapper` / `parser`; remove legacy lift + warning
  requirements; reject leftover `type:` with a migration pointer.
- `payload`: Select DataMappers via nested type-as-key only (drop deprecated `mapper.type` selection wording).
- `payload-parser`: Select PayloadParsers via nested type-as-key only; drop deprecated lift / flat `parser.type`
  scenarios (including legacy `allowed_context_url` lift).

## Impact

- `middleware/payload` `MapperConfig` + registry tests
- `middleware/parsing` `ParserConfig` + parser config tests
- Example/Helm YAML only if any leftover `type:` remains (expect none)
- OpenSpec deltas above
- Follow-up: close #478 on merge
