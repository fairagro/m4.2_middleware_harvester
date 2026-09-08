# Project Principles

This repository extends the shared foundation in
[`principles.global.md`](principles.global.md). Read that file first for Values,
Supported development environment, Type Safety, Configuration, Code Quality,
Testing, Security, Spec/Code naming, Python tooling, and Branch strategy.

Do **not** redefine or weaken Supported development environment or Type Safety
here — those sections are owned by `principles.global.md`.

Product stack, plugin contract, module graph, and harvester-specific constraints
live below. Surface-bar path rows for this product belong in
[`docs/surface-quality-bar.md`](../docs/surface-quality-bar.md) (not here).

---

## Foundation Contract

The authoritative contract for each harvesting plugin is the mapping domain
under `openspec/specs/` (e.g.
[inspire-to-arc-mapping](specs/inspire-to-arc-mapping/)).
Each document defines the source metadata fields, how they map to ARC concepts,
and required/optional semantics. **All feature specs assume these documents as
given.** Feature specs do not restate mapping rules; they reference the relevant
spec when they need to cite a field or constraint.

The central orchestrator (`middleware/harvester`) never parses source-format
records directly. Each plugin owns its own parsing, modelling, and mapping logic
entirely.

Feature specs SHALL treat the mapping documents linked from these principles as
the authoritative source→ARC contract, and SHALL reference those documents
instead of restating mapping rules. Implementations SHALL honour the Values,
Constraints, and Module Dependency Graph documented here and in
`principles.global.md`.

---

## Purpose

Harvest metadata from heterogeneous external sources, translate the records into
the Annotated Research Context (ARC) format, and publish the results to the
FAIRagro Middleware API.

The system is built around a **plugin architecture**: each input format is
implemented as a self-contained async-generator plugin. The central orchestrator
loads a unified configuration, dispatches to the appropriate plugins, consumes
their ARC output, and uploads it to the API. Adding a new input format means
adding a new plugin — the orchestrator requires no changes.

---

## Technology Stack

| Technology | Role |
| ---------- | ---- |
| **Python 3.12+** | Primary language |
| **uv** | Package manager / runner (never pip directly) |
| **arctrl** | ARC object model and RO-Crate JSON-LD serialization |
| **owslib** | CSW 2.0.2 client (INSPIRE plugin) |
| **rdflib** | RDF graphs for linked-data plugins |
| **Docker** | Containerization / deployment |

Package manager: always `uv` (never pip/poetry directly). See also Python
tooling in `principles.global.md`.

---

## Values (product)

Shared values are in `principles.global.md`. This repo additionally emphasises:

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

**Domain over plumbing** — Harvesting semantics (discovery, mapping, error
meaning) stay readable as domain code. Concurrency, backpressure, retries, HTTP
politeness wrappers, and similar mechanics live in dedicated modules and are
wired via narrow callbacks or ports — not mixed into the same methods that encode
what a source means. Extract plumbing when it obscures the harvest steps; do not
extract every trivial `asyncio` call.

---

## Constraints (product)

Shared Type Safety, Configuration, and quality-tool identity rules are in
`principles.global.md`. In this repo:

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
  Tool invocations (IDE, pre-commit, CI) must produce identical results via
  shared config (`pyproject.toml` / `.bandit`) and `uv run` / locked versions.
  The merge type-check gate is **mypy** (`uv run mypy --config-file pyproject.toml`).
- No `noqa` / `type: ignore` suppressions unless technically unavoidable.
- Validation belongs in Pydantic models where possible. Use `Literal` types or
  `@field_validator` to enforce valid values — a `ValidationError` triggers the
  standard skip-with-yield-error path. Only write custom error code outside
  Pydantic when a spec violation should log a warning but NOT skip the record.
- Within a plugin package, separate **domain modules** (mapper, dataset, sitemap,
  models) from **infrastructure modules** (bounded pipelines, retry loops, shared
  HTTP wrappers used as composition targets). Plugin entrypoints (`plugin.py`) MAY
  compose both, but MUST NOT grow large blocks of asyncio lifecycle / queue /
  cancellation logic alongside mapping rules. Prefer extracting plumbing when it
  obscures the harvest steps. Do not invent harvester-wide generic frameworks
  until a second plugin needs the same mechanism (YAGNI).

Plugin packages SHALL keep harvest domain logic in domain-oriented modules and
SHALL place substantial concurrency / backpressure / retry / cancellation
mechanics in dedicated infrastructure modules. Package-local plumbing MUST NOT
be promoted to `middleware/harvester` solely for speculative reuse.

---

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

# Linked Data plugin — domain wiring vs concurrency plumbing
linked_data/plugin.py   →  linked_data/pipeline.py   # bounded producer/worker/consumer
linked_data/plugin.py   →  linked_data/sitemap.py / dataset / linked_data_mapper
linked_data/pipeline.py ↛  linked_data_mapper / dataset implementations
# pipeline may import DiscoveryResult (and related types) from the dataset
# package; ``dataset/__init__.py`` MUST NOT eagerly import provider dataset
# classes. Pipeline MUST NOT perform mapping or own source-format semantics.

config  ←── all modules (read-only)
```

Circular imports are forbidden. Within a plugin, the mapper must not import the
source client and vice versa. Plugins must not import each other. Infrastructure
modules MUST NOT import mappers or execute mapping logic.

---

## Configuration (product)

Shared rules are in `principles.global.md`. In this repo:

- Runtime configuration is read from YAML via `ConfigWrapper` /
  product `Config` models (`middleware.shared` + harvester/plugin configs).
- **No `os.environ` calls in application code.** Environment variables are
  resolved by the config layer only.
- Every configurable value must have a Pydantic field with a `description`.
- Defaults belong in `Config`, not in application code.
- See the `config-wrapper` skill for the full pattern.

---

## Extension Points

| Need | Where to change |
| --- | --- |
| New input format / source type | Add a new plugin package under `middleware/`, implement `run_plugin(config) → AsyncGenerator` |
| New config value (orchestrator) | Extend `HarvesterConfig` in `middleware/harvester/config.py` |
| New config value (plugin) | Extend the plugin's `Config` class in its own `config.py` |
| New source field (existing plugin) | Add field to the plugin's record model, extract in client, map in mapper |
| New ARC structure | Add helper method to the plugin's mapper; reference arctrl skill |

---

## Spec / Code Naming (product)

- Capability specs live under `openspec/specs/<domain>/` with kebab-case domain
  names.
- Behaviour-oriented domains need not map 1:1 to a class.
- Stable architecture notes may live as `openspec/specs/<domain>/design.md`.
- Shared foundation: `openspec/principles.global.md` (synced). Product overlay:
  this file.
