# OTLP Observability

The harvester sends structured traces via OTLP to an OpenTelemetry collector
whenever an endpoint is configured. When no endpoint is configured the feature
is a complete no-op — no performance cost, no side-effects.

## Requirements

- [ ] When `otel.endpoint` is `None` the application initialises no tracing
      infrastructure and no spans are emitted.
- [ ] When `otel.endpoint` is set, `initialize_tracing` and `initialize_logging`
      from `middleware.shared.tracing` are called once at process start, before
      the orchestration loop begins.
- [ ] The service name passed to both initialisation functions is the constant
      string `"middleware-harvester"`.
- [ ] The orchestrator emits a root span named `harvest_run` that encloses the
      entire orchestration loop and carries the attribute
      `harvester.repository_count` (integer — total number of configured
      repositories).
- [ ] For each repository the orchestrator emits a child span named `plugin_run`
      with attributes `harvester.plugin_type` (string) and
      `harvester.repository_rdi` (string).
- [ ] For each successful API upload the orchestrator emits a child span of
      `plugin_run` named `arc_upload` with attribute `harvester.arc_id` (string).
- [ ] A `plugin_run` span records `harvester.arcs_uploaded` (integer — number of
      successfully uploaded ARCs for that repository).
- [ ] A `plugin_run` span sets its status to `ERROR` when the repository loop
      raises an unhandled exception, and records the exception on the span.
- [ ] An `arc_upload` span sets its status to `ERROR` when the API call fails,
      and records the exception on the span.
- [ ] The `TracerProvider` is explicitly shut down (flushing pending spans) before
      the process exits, regardless of whether the run succeeded or failed.
- [ ] `otel.log_console_spans` controls whether spans are additionally written to
      the console log (`log_console_spans=True` → `SimpleConsoleSpanExporter`
      active). Default is `False`.
- [ ] All tracing code is confined to `middleware/harvester/src/middleware/harvester/main.py`.
      Plugin modules have no direct dependency on any OpenTelemetry package.

## Edge Cases

`otel.endpoint` is set but the collector is unreachable at startup →
`initialize_tracing` logs a warning and continues; the harvest run proceeds
without OTLP export.

`otel.endpoint` is set but the collector becomes unreachable mid-run →
`BatchSpanProcessor` buffers and retries internally; the harvest run is not
interrupted.

Config file does not contain an `otel` block → Pydantic default (`OtelConfig()`
with `endpoint=None`) applies; behaviour is identical to explicit `otel.endpoint:
null`.
