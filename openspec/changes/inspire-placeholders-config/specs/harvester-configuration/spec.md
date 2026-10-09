# Spec Delta

## MODIFIED Requirements

### Requirement: Placeholder values MUST be configurable per repository

Placeholders MUST be configured as a `placeholders` object (`middleware.payload.placeholders` `PlaceholderConfig`):
`values`, the whole-value placeholders this RDI writes instead of leaving a field empty, and `unrendered_templates`,
whether unrendered `$var`, `${var}` and `{{var}}` templates also count. The block MUST sit where the check runs: the
`inspire` plugin block for INSPIRE (`inspire.placeholders`, read by the parser), and the `mapper` block for
`linked_data`, `generic` and `oai_pmh` (`mapper.placeholders`, read by the mapper). The defaults MUST live on the model
and MUST be empty (`values: []`, `unrendered_templates: false`), so nothing is treated as a placeholder unless the
operator configures it. Values MUST be compared trimmed and case-insensitive. Code that receives the placeholders
(parsers, clients, mappers) MUST take a config object holding the `PlaceholderConfig` and MUST NOT supply its own
default.

#### Scenario: Per-RDI values

- **WHEN** a repository sets `mapper.placeholders.values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder values are `{"keine angabe"}`

#### Scenario: INSPIRE placeholders on the plugin block

- **WHEN** an `inspire` repository sets `inspire.placeholders.values: ["None"]`
- **THEN** configuration validation succeeds without a warning and the INSPIRE parser treats "None" as a placeholder

#### Scenario: No placeholders by default

- **WHEN** a repository sets no `placeholders`
- **THEN** no value counts as a placeholder, including "None" and `$licenseURL`

## ADDED Requirements

### Requirement: mapper.placeholders on inspire repositories is deprecated

When an `inspire` repository explicitly sets `mapper.placeholders`, configuration validation MUST succeed, MUST emit a
`logger.warning` pointing at `inspire.placeholders`, and MUST use that value as `inspire.placeholders`. When both are
set and differ, validation MUST fail. An unset `mapper.placeholders` MUST NOT warn. Repositories of other plugins MUST
keep reading `mapper.placeholders` unchanged.

#### Scenario: Legacy location is lifted

- **WHEN** an `inspire` repository sets `mapper.placeholders.values: ["None"]` and no `inspire.placeholders`
- **THEN** validation succeeds, a deprecation warning is logged, and `inspire.placeholders.values` is `{"none"}`

#### Scenario: Conflicting locations

- **WHEN** an `inspire` repository sets `mapper.placeholders.values: ["None"]` and
  `inspire.placeholders.values: ["n/a"]`
- **THEN** configuration validation fails naming both fields

#### Scenario: Linked-data repository is unaffected

- **WHEN** a `generic` repository sets `mapper.placeholders.unrendered_templates: true`
- **THEN** no deprecation warning is logged and the mapper receives that `PlaceholderConfig`
