# Harvester Error Handling

Defines a project-wide, standardized exception hierarchy for the core orchestrator and all harvesting plugins, as well as the paradigm of "yielding" errors to the orchestrator.

## Requirements

- [ ] Provide a central base exception class `HarvesterError` in `middleware.harvester.errors`.
- [ ] Provide a global `RecordProcessingError` inheriting from `HarvesterError` inside `middleware.harvester.errors` that carries structured record context (`record_id`, optional `original_error`).
- [ ] Each plugin MUST define its own plugin-specific base exception (e.g., `InspireError`, `SchemaOrgError`) that inherits directly from `HarvesterError`. All further plugin-internal exception classes MUST inherit from that plugin-specific base — never directly from `HarvesterError`.
- [ ] The `AsyncGenerator` contract of every plugin MUST be `AsyncGenerator[str | HarvesterError, None]`.
- [ ] Plugins MUST NOT swallow or locally log expected record-level parsing or mapping failures. Instead, they must `yield` a `HarvesterError` instance to the orchestrator.
- [ ] When a record identifier is available at the time of failure, plugins MUST yield `RecordProcessingError` (not the plugin-specific base type), so the orchestrator can extract a structured `record_id` for telemetry.
- [ ] Fatal setup or configuration failures (unreachable endpoint, unsupported plugin type) that prevent the plugin from producing any records MUST be raised as standard Python exceptions (`ValueError`, `OSError`) or a `HarvesterError` subclass — not yielded. The orchestrator treats a raised exception as a full plugin failure.
- [ ] Standard Python exceptions (`ValueError`, `TypeError`, `KeyError`) MUST be used for programming errors (wrong argument type, unsupported enum value in configuration). These MUST NOT be wrapped in `HarvesterError`.
- [ ] The central orchestrator is solely responsible for consuming, interpreting, and logging all yielded `HarvesterError`s and any raised exceptions from plugins, ensuring centralized telemetry output.

## Edge Cases

A plugin yields a `HarvesterError` subclass that is not a `RecordProcessingError` (record identifier unavailable at failure time) → orchestrator logs it as a record-level failure without structured `record_id` context.

A plugin raises an uncaught exception during iteration → orchestrator catches it, marks the plugin as failed, logs the exception; other plugins continue unaffected.

A fatal error occurs before any records are produced (e.g., endpoint unreachable) → plugin raises, not yields, so the orchestrator receives no partial output and can clearly distinguish a full plugin failure from partial record failures.
