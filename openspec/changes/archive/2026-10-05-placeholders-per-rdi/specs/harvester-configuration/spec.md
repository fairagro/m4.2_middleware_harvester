## ADDED Requirements

### Requirement: Placeholder values MUST be configurable per repository

The repository `mapper` block MUST accept an optional `placeholders` object (`middleware.payload.placeholders`
`PlaceholderConfig`): `values`, the whole-value placeholders this RDI writes instead of leaving a field empty, and
`unrendered_templates`, whether unrendered `$var`, `${var}` and `{{var}}` templates also count. The defaults MUST live
on the model and MUST be empty (`values: []`, `unrendered_templates: false`), so nothing is treated as a placeholder
unless the operator configures it. Values MUST be compared trimmed and case-insensitive. Code that receives the
placeholders (parsers, clients, mappers) MUST take the `PlaceholderConfig` object and MUST NOT supply its own default.
The same field MUST apply to every plugin (`inspire`, `linked_data`, `generic`, `oai_pmh`).

#### Scenario: Per-RDI values

- **WHEN** a repository sets `mapper.placeholders.values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder values are `{"keine angabe"}`

#### Scenario: No placeholders by default

- **WHEN** a repository omits `mapper.placeholders`
- **THEN** no value counts as a placeholder, including "None" and `$licenseURL`
