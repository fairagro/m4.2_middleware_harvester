# Harvester Error Handling — Design

## Exception Hierarchy

- `Exception`
  - `HarvesterError` (`middleware.harvester.errors` — shared root)
    - `RecordProcessingError` (global standard for record-level failures, carries `record_id`)
    - `InspireError` (`middleware.inspire.errors` — inspire plugin base)
      - `CswConnectionError`
      - `SemanticError`
    - `SchemaOrgError` (`middleware.schema_org.errors` — schema.org plugin base, not yet implemented)

## Key Decisions

1. **Centralized `HarvesterError` root class**
   — By defining a single root exception, the project enforces a type-safe boundary between domain exceptions and raw system faults (`KeyError`, `MemoryError`). The orchestrator can catch all domain failures with a single `except HarvesterError` branch.

2. **Yielding errors over raising them for record-level failures**
   — Since plugins operate as `AsyncGenerator`s, `raise`ing an exception terminates the execution loop instantly, violating the "Failure isolation" principle. Plugins `yield` `HarvesterError` instances to the orchestrator instead. This centralizes logging inside the orchestrator and delegates the decision of how to report failures away from individual plugins.

3. **Fatal vs. record-level failures**
   — Record-level failures (one record cannot be parsed or mapped) are yielded as `RecordProcessingError`; the generator continues. Fatal failures (endpoint unreachable, plugin misconfigured before any record is produced) are raised as standard Python exceptions or `HarvesterError` subclasses, exiting the generator entirely. The orchestrator treats raised exceptions as full plugin failures and yielded errors as partial failures. This two-tier model lets the orchestrator distinguish "some records failed" from "the entire plugin is broken".

4. **Standard Python exceptions for programming errors**
   — `ValueError`, `TypeError`, and `KeyError` are used for errors that indicate incorrect usage by the developer (wrong enum value in configuration, bad argument type). These are not wrapped in `HarvesterError` because they signal a bug in the calling code, not a runtime domain failure. They should be fixed at development time, not caught in production.

5. **`RecordProcessingError` preferred over plugin-specific base for record failures**
   — When a record identifier is known at failure time, plugins yield `RecordProcessingError` rather than the plugin-specific base exception, because it carries a structured `record_id` field. This allows the orchestrator to emit structured telemetry without inspecting the concrete exception type.

6. **Mandatory plugin-specific base exception**
   — Each plugin defines its own base exception (e.g., `InspireError`, `SchemaOrgError`) so that consumers can catch all failures originating from a specific plugin with one `except` clause, independent of `RecordProcessingError`. It also makes stack traces immediately identifiable by plugin origin.
