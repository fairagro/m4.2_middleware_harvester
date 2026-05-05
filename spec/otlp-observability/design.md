# OTLP Observability — Design

## Module Overview

All tracing initialisation and span management is concentrated in
`middleware/harvester/src/middleware/harvester/main.py`. The two functions
`initialize_tracing` and `initialize_logging` from `middleware.shared.tracing`
are the only entry points used. Plugins have no tracing dependency.

```text
main.py
  └─ initialize_tracing()   (middleware.shared.tracing)
  └─ initialize_logging()   (middleware.shared.tracing)
  └─ run_orchestrator()
       └─ harvest_run span
            └─ plugin_run span  (per repository)
                 └─ arc_upload span  (per successful upload)
```

## Key Decisions

1. **`middleware.shared.tracing` used as-is, without modification**
   — The shared library already implements `initialize_tracing` /
   `initialize_logging` using the OpenTelemetry SDK. Replacing or wrapping it
   (e.g. with logfire) is explicitly deferred: the harvester only calls the
   public function signatures, never stores `TracerProvider` instances, and uses
   only the standard `opentelemetry.trace` API for span creation. This means the
   internal implementation of the shared library can be swapped for logfire at a
   later point without any changes required in this repository.

2. **Tracing is confined to `main.py`; plugins are tracing-free**
   — Plugins expose an `AsyncGenerator` contract and must not be coupled to any
   observability framework. The orchestrator in `main.py` is the sole consumer of
   plugin output and the natural place to emit spans. This preserves the
   Failure-isolation principle: a tracing misconfiguration cannot break plugin
   execution.

3. **`service_name` is a hard-coded constant, not a config field**
   — `OtelConfig` already covers runtime-variable settings (`endpoint`,
   `log_console_spans`, `log_level`). The service name identifies the deployment
   unit and never changes at runtime; adding it to `OtelConfig` would expose a
   configuration knob that has no valid user-facing variation.

4. **`TracerProvider.shutdown()` is called explicitly before process exit**
   — The harvester is a short-lived cron process. Without an explicit shutdown the
   `BatchSpanProcessor` may not flush its buffer before the OS reclaims the
   process. A `try/finally` block in `main()` guarantees flush on both clean exit
   and unhandled exceptions.

5. **OTLP Metrics are out of scope**
   — Metrics require a long-lived process to accumulate meaningful data.
   For a cron-driven process, counter values reset on every invocation and
   provide no cross-run trending without additional aggregation infrastructure.
   Traces carry all per-run quantitative data as span attributes
   (`harvester.arcs_uploaded`, `harvester.repository_count`), which is sufficient
   for alerting and debugging. Metrics may be revisited if the harvester is ever
   run as a persistent service.
