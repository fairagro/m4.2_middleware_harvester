# OTLP Observability

## Purpose

The harvester sends structured traces via OTLP to an OpenTelemetry collector
whenever an endpoint is configured. When no endpoint is configured the feature
is a complete no-op — no performance cost, no side-effects.

## Requirements

### Requirement: When otel.endpoint is None the application initialises no tracing
The system SHALL ensure that when `otel.endpoint` is `None` the application initialises no tracing.

#### Scenario: Satisfies — When otel.endpoint is None the application initialises no tracing
- **WHEN** the conditions described by this requirement apply
- **THEN** When `otel.endpoint` is `None` the application initialises no tracing

### Requirement: When otel.endpoint is set, initialize_tracing and initialize_logging
The system SHALL ensure that when `otel.endpoint` is set, `initialize_tracing` and `initialize_logging`.

#### Scenario: Satisfies — When otel.endpoint is set, initialize_tracing and initialize_logging
- **WHEN** the conditions described by this requirement apply
- **THEN** When `otel.endpoint` is set, `initialize_tracing` and `initialize_logging`

### Requirement: The service name passed to both initialisation functions is the…
The service name passed to both initialisation functions SHALL be the constant.

#### Scenario: Satisfies — The service name passed to both initialisation functions is the…
- **WHEN** the conditions described by this requirement apply
- **THEN** The service name passed to both initialisation functions is the constant

### Requirement: The orchestrator emits a root span named harvest_run that encloses…
The system SHALL ensure that the orchestrator emits a root span named `harvest_run` that encloses the.

#### Scenario: Satisfies — The orchestrator emits a root span named harvest_run that encloses…
- **WHEN** the conditions described by this requirement apply
- **THEN** The orchestrator emits a root span named `harvest_run` that encloses the

### Requirement: For each repository the orchestrator emits a child span named…
The system SHALL ensure that for each repository the orchestrator emits a child span named `plugin_run`.

#### Scenario: Satisfies — For each repository the orchestrator emits a child span named…
- **WHEN** the conditions described by this requirement apply
- **THEN** For each repository the orchestrator emits a child span named `plugin_run`

### Requirement: For each repository the orchestrator emits a child span of…
The system SHALL ensure that for each repository the orchestrator emits a child span of `plugin_run`.

#### Scenario: Satisfies — For each repository the orchestrator emits a child span of…
- **WHEN** the conditions described by this requirement apply
- **THEN** For each repository the orchestrator emits a child span of `plugin_run`

### Requirement: A plugin_run span records harvester.arcs_uploaded (integer — number of
The system SHALL ensure that a `plugin_run` span records `harvester.arcs_uploaded` (integer — number of.

#### Scenario: Satisfies — A plugin_run span records harvester.arcs_uploaded (integer — number of
- **WHEN** the conditions described by this requirement apply
- **THEN** A `plugin_run` span records `harvester.arcs_uploaded` (integer — number of

### Requirement: A plugin_run span sets its status to ERROR when the…
The system SHALL ensure that a `plugin_run` span sets its status to `ERROR` when the repository loop.

#### Scenario: Satisfies — A plugin_run span sets its status to ERROR when the…
- **WHEN** the conditions described by this requirement apply
- **THEN** A `plugin_run` span sets its status to `ERROR` when the repository loop

### Requirement: A harvest_upload span sets its status to ERROR when the…
The system SHALL ensure that a `harvest_upload` span sets its status to `ERROR` when the `harvest_arcs`.

#### Scenario: Satisfies — A harvest_upload span sets its status to ERROR when the…
- **WHEN** the conditions described by this requirement apply
- **THEN** A `harvest_upload` span sets its status to `ERROR` when the `harvest_arcs`

### Requirement: The TracerProvider is explicitly shut down (flushing pending spans) before
The `TracerProvider` SHALL be explicitly shut down (flushing pending spans) before.

#### Scenario: Satisfies — The TracerProvider is explicitly shut down (flushing pending spans) before
- **WHEN** the conditions described by this requirement apply
- **THEN** The `TracerProvider` is explicitly shut down (flushing pending spans) before

### Requirement: Otel.log_console_spans controls whether spans are additionally written to
The system SHALL ensure that `otel.log_console_spans` controls whether spans are additionally written to.

#### Scenario: Satisfies — Otel.log_console_spans controls whether spans are additionally written to
- **WHEN** the conditions described by this requirement apply
- **THEN** `otel.log_console_spans` controls whether spans are additionally written to

### Requirement: Tracing stays in the harvester orchestrator, not in plugins
The system SHALL confine tracing initialisation and span creation to the
harvester entrypoint (`main.py`) and orchestrator/upload modules. Plugins
MUST NOT depend on OpenTelemetry.

#### Scenario: Plugins remain tracing-free

- **WHEN** a harvesting plugin runs
- **THEN** it does not import or call OpenTelemetry APIs; spans are created by
  the orchestrator/upload layer around plugin invocation

### Requirement: Edge case — Otel.endpoint is set but the collector is unreachable at startup
The system SHALL handle this edge case: when `otel.endpoint` is set but the collector is unreachable at startup, then `initialize_tracing` logs a warning and continues; the harvest run proceeds without OTLP export.

#### Scenario: Edge case — Otel.endpoint is set but the collector is unreachable at startup
- **WHEN** `otel.endpoint` is set but the collector is unreachable at startup
- **THEN** `initialize_tracing` logs a warning and continues; the harvest run proceeds without OTLP export

### Requirement: Edge case — Otel.endpoint is set but the collector becomes unreachable mid-run
The system SHALL handle this edge case: when `otel.endpoint` is set but the collector becomes unreachable mid-run, then `BatchSpanProcessor` buffers and retries internally; the harvest run is not interrupted.

#### Scenario: Edge case — Otel.endpoint is set but the collector becomes unreachable mid-run
- **WHEN** `otel.endpoint` is set but the collector becomes unreachable mid-run
- **THEN** `BatchSpanProcessor` buffers and retries internally; the harvest run is not interrupted

### Requirement: Edge case — Config file does not contain an otel block
The system SHALL handle this edge case: when Config file does not contain an `otel` block, then Pydantic default (`OtelConfig()` with `endpoint=None`) applies; behaviour is identical to explicit `otel.endpoint: null`.

#### Scenario: Edge case — Config file does not contain an otel block
- **WHEN** Config file does not contain an `otel` block
- **THEN** Pydantic default (`OtelConfig()` with `endpoint=None`) applies; behaviour is identical to explicit `otel.endpoint: null`
