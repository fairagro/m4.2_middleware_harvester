# Project Principles

## Purpose

Authoritative project principles and foundation contract for the FAIRagro Middleware Harvester. All feature specs assume this document as given.

## Requirements

### Requirement: Follow the foundation contract
All harvesting plugins SHALL treat the mapping documents linked from the principles as the authoritative source→ARC contract, and feature specs SHALL reference those documents instead of restating mapping rules.

#### Scenario: Feature specs reference mapping docs
- **WHEN** a feature spec needs to cite a mapped field or constraint
- **THEN** it references the relevant mapping spec instead of restating rules

### Requirement: Honour project values and constraints
Implementations SHALL honour the Values, Constraints, and Module Dependency Graph documented in the project principles.

#### Scenario: Code changes respect principles
- **WHEN** code is added or modified
- **THEN** it complies with the Values, Constraints, and dependency rules in the principles document

## Full Principles

# FAIRagro Middleware Harvester — Principles

## Foundation Contract

The authoritative contract for each harvesting plugin is the mapping domain
under `openspec/specs/` (e.g.
[inspire-to-arc-mapping](../inspire-to-arc-mapping/)).
Each document defines the source metadata fields, how they map to ARC concepts,
and required/optional semantics. **All feature specs assume these documents as
given.** Feature specs do not restate mapping rules; they reference the relevant
spec when they need to cite a field or constraint.

The central orchestrator (`middleware/harvester`) never parses source-format
records directly. Each plugin owns its own parsing, modelling, and mapping logic
entirely.

## Purpose

Harvest metadata from heterogeneous external sources, translate the records into
the Annotated Research Context (ARC) format, and publish the results to the
FAIRagro Middleware API.

The system is built around a **plugin architecture**: each input format (currently
INSPIRE/CSW) is implemented as a self-contained async-generator plugin. The
central orchestrator loads a unified configuration, dispatches to the appropriate
plugins, consumes their ARC output, and uploads it to the API. Adding a new input
format means adding a new plugin — the orchestrator requires no changes.

## Values

**Correctness over speed** — Valid ARC output matters more than throughput.
If a record cannot be mapped cleanly it must fail with a clear error, not produce
silent garbage.

**Memory-safe by design** — Source endpoints can contain millions of records.
Each plugin must use pagination or streaming; the in-memory footprint per batch
must be bounded and predictable.

**Failure isolation** — One bad record must not abort the entire harvest run.
Plugins `yield` `HarvesterError` instances to the orchestrator instead of raising.
The orchestrator is solely responsible for logging and telemetry.

**Stateless harvest process** — The harvester stores no state between runs.
No cache, no lock files, no local database writes. The only persistent output is
what the Middleware API receives.

**Security by default** — Inputs from external sources (endpoints, API, config)
are treated as untrusted. Follow OWASP best practices: validate before use, fail
closed, apply least privilege.

## Constraints

- Python 3.12. No type-unsafe workarounds; all public APIs are fully typed.
- `uv` for dependency management. Never call `pip` directly in production code.
- `os.environ` must never be accessed directly; use `Config` / `ConfigWrapper`.
- Each plugin owns its source-format access exclusively. The orchestrator and
  other plugins must not reach into another plugin's internals.
- The plugin `AsyncGenerator` contract is
  `AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]`.
  Plugins yield `HarvestedArc` (serialized ARC JSON plus study/assay counts and
  optional source URL) on success and `HarvesterError` / `SkippedRecord` for
  record-level outcomes — never raise for expected failures.
- All plugin-specific exceptions inherit from `HarvesterError`
  (defined in `middleware.harvester.errors`).
- Code quality gates: Ruff (lint + format), mypy, pylint, bandit, pytest —
  all must pass before merge. Every new feature requires matching tests.
- **All quality tool invocations (VS Code / Cursor, pre-commit, CI) must produce
  identical results.** This is achieved by having each tool read its configuration
  exclusively from a single shared config file — normally `pyproject.toml`
  (`[tool.ruff]`, `[tool.mypy]`, `[tool.pylint.*]`). Tools that cannot be configured
  via `pyproject.toml` (e.g. bandit) must have a dedicated config file (e.g. `.bandit`)
  shared by all invocations. Individual invocations must contain no extra CLI flags
  that override shared config; the only acceptable flags are those that cannot be
  expressed in a config file. The tool version used in every context must be the one
  locked in `uv.lock` — use `uv run <tool>` everywhere.
  For type checking specifically: the merge gate is **mypy**
  (`uv run mypy --config-file pyproject.toml middleware/`). The IDE must run the
  same via `ms-python.mypy-type-checker` (see `.vscode/settings.json`: same binary,
  same config file, same `middleware/` target, `reportingScope=workspace`).
  cursorpyright / Pylance diagnostics are not a substitute and must not be treated
  as “type check passed”.
- No `noqa` / `type: ignore` suppressions unless technically unavoidable.
- Validation belongs in Pydantic models where possible. Use `Literal` types or
  `@field_validator` to enforce valid values — a `ValidationError` triggers the
  standard skip-with-yield-error path. Only write custom error code outside
  Pydantic when a spec violation should log a warning but NOT skip the record.

## Module Dependency Graph

```text
# Orchestrator
harvester/main.py          →  harvester/orchestrator.py
harvester/main.py          →  harvester/reporting.py
harvester/orchestrator.py  →  harvester/config.py
harvester/orchestrator.py  →  harvester/errors.py
harvester/orchestrator.py  →  harvester/upload.py
harvester/orchestrator.py  →  <plugin>/plugin.py  (dynamic dispatch by plugin key)
harvester/upload.py        →  harvester/reporting.py
harvester/upload.py        →  harvester/plugin_base.py
harvester/upload.py        →  api_client (shared lib)

# INSPIRE plugin (example; all plugins follow this pattern)
inspire/plugin.py  →  inspire/csw_client.py  →  inspire/models.py
inspire/plugin.py  →  inspire/mapper.py      →  inspire/models.py
inspire/plugin.py  →  inspire/config.py
inspire/plugin.py  →  harvester/errors.py

config  ←── all modules (read-only)
```

Circular imports are forbidden. Within a plugin, the mapper must not import the
source client and vice versa. Plugins must not import each other.

## Extension Points

| Need | Where to change |
| --- | --- |
| New input format / source type | Add a new plugin package under `middleware/`, implement `run_plugin(config) → AsyncGenerator` |
| New config value (orchestrator) | Extend `HarvesterConfig` in `middleware/harvester/config.py` |
| New config value (plugin) | Extend the plugin's `Config` class in its own `config.py` |
| New source field (existing plugin) | Add field to the plugin's record model, extract in client, map in mapper |
| New ARC structure | Add helper method to the plugin's mapper; reference arctrl skill |
