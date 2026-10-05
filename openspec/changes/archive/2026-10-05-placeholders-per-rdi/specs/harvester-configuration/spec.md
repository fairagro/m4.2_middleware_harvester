## ADDED Requirements

### Requirement: Placeholder values MUST be configurable per repository

The repository `mapper` block MUST accept an optional `placeholder_values` list of strings: the whole-value placeholders
this RDI writes instead of leaving a field empty. The default MUST be `middleware.payload.placeholders`
`DEFAULT_PLACEHOLDER_VALUES`; a configured list MUST replace the defaults. Values MUST be compared trimmed and
case-insensitive. The same field MUST apply to every plugin (`inspire`, `linked_data`, `generic`, `oai_pmh`).

#### Scenario: Per-RDI list

- **WHEN** a repository sets `mapper.placeholder_values: [" Keine Angabe "]`
- **THEN** configuration validation succeeds and that repository's placeholder list is `{"keine angabe"}`

#### Scenario: Default list

- **WHEN** a repository omits `mapper.placeholder_values`
- **THEN** its placeholder list is `DEFAULT_PLACEHOLDER_VALUES`
