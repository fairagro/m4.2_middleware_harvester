# Spec Delta

## MODIFIED Requirements

### Requirement: SkippedRecord signal type

The system SHALL provide a `SkippedRecord` class in `middleware.contracts.errors` that carries a human-readable `reason`
and an optional `url`.

#### Scenario: Class is available to plugins and orchestrator

- **WHEN** a plugin or the orchestrator needs to signal a deliberate skip
- **THEN** it uses `SkippedRecord` from `middleware.contracts.errors`
