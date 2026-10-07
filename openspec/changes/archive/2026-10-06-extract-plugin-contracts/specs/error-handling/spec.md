# Spec Delta

## MODIFIED Requirements

### Requirement: Provide a central base exception class HarvesterError in middleware.contracts.errors

The system SHALL provide a central base exception class `HarvesterError` in `middleware.contracts.errors`.

#### Scenario: Satisfies — Provide a central base exception class HarvesterError in middleware.contracts.errors

- **WHEN** a plugin or the orchestrator needs the shared harvest error base
- **THEN** it uses `HarvesterError` from `middleware.contracts.errors`

### Requirement: Provide a global RecordProcessingError inheriting from HarvesterError inside middleware.contracts.errors that…

The system SHALL provide a global `RecordProcessingError` inheriting from `HarvesterError` inside
`middleware.contracts.errors` that carries structured record context (`record_id`, optional `original_error`).

#### Scenario: Satisfies — Provide a global RecordProcessingError inheriting from HarvesterError inside middleware.contracts.errors that…

- **WHEN** a plugin reports a per-record processing failure
- **THEN** it uses `RecordProcessingError` from `middleware.contracts.errors` that carries structured record context
  (`record_id`, optional `original_error`)
