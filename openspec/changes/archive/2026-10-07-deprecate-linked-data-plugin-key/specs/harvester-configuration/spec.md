# Spec Delta

## ADDED Requirements

### Requirement: linked_data plugin key emits deprecation warning

The system SHALL treat the repository plugin key `linked_data` as deprecated in favour of `generic` with nested
`protocol` and sibling `parser` / `mapper`. When a repository entry sets `linked_data`, configuration validation MUST
succeed and MUST emit a `logger.warning` that points operators at the `generic` migration path. The warning MUST NOT
block harvest. Behaviour of the linked_data plugin and its shims MUST remain unchanged aside from the warning.

#### Scenario: linked_data repository warns and still validates

- **WHEN** a repository entry sets exactly one plugin key `linked_data` with a valid sibling `mapper` (or legacy
  `payload_type` lift)
- **THEN** configuration validation succeeds and a `logger.warning` is emitted stating that `linked_data` is deprecated
  in favour of `generic.protocol` (with sibling parser/mapper)

#### Scenario: generic repository does not emit linked_data plugin-key warning

- **WHEN** a repository entry sets exactly one plugin key `generic` (and not `linked_data`)
- **THEN** configuration validation MUST NOT emit the linked_data plugin-key deprecation warning
