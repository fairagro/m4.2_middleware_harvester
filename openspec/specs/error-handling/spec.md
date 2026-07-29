# Harvester Error Handling

## Purpose

Defines a project-wide, standardized exception hierarchy for the core orchestrator and all harvesting plugins, as well as the paradigm of "yielding" errors to the orchestrator.

## Requirements

### Requirement: Provide a central base exception class HarvesterError in middleware.harvester.errors
The system SHALL provide a central base exception class `HarvesterError` in `middleware.harvester.errors`.

#### Scenario: Satisfies — Provide a central base exception class HarvesterError in middleware.harvester.errors
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a central base exception class `HarvesterError` in `middleware.harvester.errors`

### Requirement: Provide a global RecordProcessingError inheriting from HarvesterError inside middleware.harvester.errors that…
The system SHALL provide a global `RecordProcessingError` inheriting from `HarvesterError` inside `middleware.harvester.errors` that carries structured record context (`record_id`, optional `original_error`).

#### Scenario: Satisfies — Provide a global RecordProcessingError inheriting from HarvesterError inside middleware.harvester.errors that…
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide a global `RecordProcessingError` inheriting from `HarvesterError` inside `middleware.harvester.errors` that carries structured record context (`record_id`, optional `original_error`)

### Requirement: Each plugin MUST define its own plugin-specific base exception (e.g.,…
Each plugin MUST define its own plugin-specific base exception (e.g., `InspireError`, `LinkedDataError`) that inherits directly from `HarvesterError`. All further plugin-internal exception classes MUST inherit from that plugin-specific base — never directly from `HarvesterError`.

#### Scenario: Satisfies — Each plugin MUST define its own plugin-specific base exception (e.g.,…
- **WHEN** the conditions described by this requirement apply
- **THEN** Each plugin MUST define its own plugin-specific base exception (e.g., `InspireError`, `LinkedDataError`) that inherits directly from `HarvesterError`. All further plugin-internal exception classes MUST inherit from that plugin-specific base — never directly from `HarvesterError`

### Requirement: The AsyncGenerator contract of every plugin MUST be AsyncGenerator[str |…
The `AsyncGenerator` contract of every plugin MUST be `AsyncGenerator[str | HarvesterError, None]`.

#### Scenario: Satisfies — The AsyncGenerator contract of every plugin MUST be AsyncGenerator[str |…
- **WHEN** the conditions described by this requirement apply
- **THEN** The `AsyncGenerator` contract of every plugin MUST be `AsyncGenerator[str | HarvesterError, None]`

### Requirement: Plugins MUST NOT swallow or locally log expected record-level parsing…
Plugins MUST NOT swallow or locally log expected record-level parsing or mapping failures. Instead, they must `yield` a `HarvesterError` instance to the orchestrator.

#### Scenario: Satisfies — Plugins MUST NOT swallow or locally log expected record-level parsing…
- **WHEN** the conditions described by this requirement apply
- **THEN** Plugins MUST NOT swallow or locally log expected record-level parsing or mapping failures. Instead, they must `yield` a `HarvesterError` instance to the orchestrator

### Requirement: When a record identifier is available at the time of…
When a record identifier is available at the time of failure, plugins MUST yield `RecordProcessingError` (not the plugin-specific base type), so the orchestrator can extract a structured `record_id` for telemetry.

#### Scenario: Satisfies — When a record identifier is available at the time of…
- **WHEN** the conditions described by this requirement apply
- **THEN** When a record identifier is available at the time of failure, plugins MUST yield `RecordProcessingError` (not the plugin-specific base type), so the orchestrator can extract a structured `record_id` for telemetry

### Requirement: Fatal setup or configuration failures (unreachable endpoint, unsupported plugin type)…
Fatal setup or configuration failures (unreachable endpoint, unsupported plugin type) that prevent the plugin from producing any records MUST be raised as standard Python exceptions (`ValueError`, `OSError`) or a `HarvesterError` subclass — not yielded. The orchestrator treats a raised exception as a full plugin failure.

#### Scenario: Satisfies — Fatal setup or configuration failures (unreachable endpoint, unsupported plugin type)…
- **WHEN** the conditions described by this requirement apply
- **THEN** Fatal setup or configuration failures (unreachable endpoint, unsupported plugin type) that prevent the plugin from producing any records MUST be raised as standard Python exceptions (`ValueError`, `OSError`) or a `HarvesterError` subclass — not yielded. The orchestrator treats a raised exception as a full plugin failure

### Requirement: Standard Python exceptions (ValueError, TypeError, KeyError) MUST be used for…
Standard Python exceptions (`ValueError`, `TypeError`, `KeyError`) MUST be used for programming errors (wrong argument type, unsupported enum value in configuration). These MUST NOT be wrapped in `HarvesterError`.

#### Scenario: Satisfies — Standard Python exceptions (ValueError, TypeError, KeyError) MUST be used for…
- **WHEN** the conditions described by this requirement apply
- **THEN** Standard Python exceptions (`ValueError`, `TypeError`, `KeyError`) MUST be used for programming errors (wrong argument type, unsupported enum value in configuration). These MUST NOT be wrapped in `HarvesterError`

### Requirement: The central orchestrator is solely responsible for consuming, interpreting, and…
The central orchestrator SHALL be solely responsible for consuming, interpreting, and logging all yielded `HarvesterError`s and any raised exceptions from plugins, ensuring centralized telemetry output.

#### Scenario: Satisfies — The central orchestrator is solely responsible for consuming, interpreting, and…
- **WHEN** the conditions described by this requirement apply
- **THEN** The central orchestrator is solely responsible for consuming, interpreting, and logging all yielded `HarvesterError`s and any raised exceptions from plugins, ensuring centralized telemetry output

### Requirement: Edge case — A plugin yields a HarvesterError subclass that is not a…
The system SHALL handle this edge case: when A plugin yields a `HarvesterError` subclass that is not a `RecordProcessingError` (record identifier unavailable at failure time), then orchestrator logs it as a record-level failure without structured `record_id` context.

#### Scenario: Edge case — A plugin yields a HarvesterError subclass that is not a…
- **WHEN** A plugin yields a `HarvesterError` subclass that is not a `RecordProcessingError` (record identifier unavailable at failure time)
- **THEN** orchestrator logs it as a record-level failure without structured `record_id` context

### Requirement: Edge case — A plugin raises an uncaught exception during iteration
The system SHALL handle this edge case: when A plugin raises an uncaught exception during iteration, then orchestrator catches it, marks the plugin as failed, logs the exception; other plugins continue unaffected.

#### Scenario: Edge case — A plugin raises an uncaught exception during iteration
- **WHEN** A plugin raises an uncaught exception during iteration
- **THEN** orchestrator catches it, marks the plugin as failed, logs the exception; other plugins continue unaffected

### Requirement: Edge case — A fatal error occurs before any records are produced (e.g.,…
The system SHALL handle this edge case: when A fatal error occurs before any records are produced (e.g., endpoint unreachable), then plugin raises, not yields, so the orchestrator receives no partial output and can clearly distinguish a full plugin failure from partial record failures.

#### Scenario: Edge case — A fatal error occurs before any records are produced (e.g.,…
- **WHEN** A fatal error occurs before any records are produced (e.g., endpoint unreachable)
- **THEN** plugin raises, not yields, so the orchestrator receives no partial output and can clearly distinguish a full plugin failure from partial record failures
