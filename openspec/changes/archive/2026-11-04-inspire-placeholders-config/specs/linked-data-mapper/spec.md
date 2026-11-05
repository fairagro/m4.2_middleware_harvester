# Spec Delta

## ADDED Requirements

### Requirement: LinkedDataMapper MUST hold the repository placeholders

`LinkedDataMapper` MUST take the repository's `PlaceholderConfig` in its constructor (no default), expose it as
`placeholders`, and provide `license(value, name=...)`, which applies
`middleware.payload.arc_license.license_from_value` with those placeholders. The base `from_config` MUST pass
`mapper.placeholders`. Subclasses MUST use the base attribute and helper instead of storing their own copy.

#### Scenario: Subclass without extra settings

- **WHEN** `GeneralSchemaOrgMapper.from_config` receives a `MapperConfig` with `placeholders.unrendered_templates: true`
- **THEN** the mapper's `placeholders` is that object and `license("$licenseURL")` returns `None`

#### Scenario: Subclass with extra settings

- **WHEN** `RegalMapper` or `CkanextDcatMapper` is built from a `MapperConfig`
- **THEN** it passes `mapper.placeholders` to the base constructor alongside its own settings
