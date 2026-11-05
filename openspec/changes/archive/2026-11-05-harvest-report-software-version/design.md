# Design

## Context

See proposal.md — Why. `main.py` already logs `version("harvester")` and exposes `--version`. `run_orchestrator`
constructs `HarvestReport()` with no version. Shared 14.2.0 adds optional `software_version` and emits
`schema:instrument` / `schema:softwareVersion` when set.

## Goals / Non-Goals

**Goals:**

- One PEP 440 string for log, CLI, and report
- Depend on published shared ≥14.2.0

**Non-Goals:**

- Forking or wrapping `JsonLdReportSerializer`
- Changing when the report is emitted

## Decisions

1. **Set version on `HarvestReport` construction in the orchestrator** — `report = HarvestReport(software_version=…)`
   (or assign immediately after). Keeps report creation as the single place that owns run-scoped report state.
   Alternative: set in `main` after `run_orchestrator` returns — rejected; late assignment risks forgetting on
   early-return paths that still emit a report (today emit only when `report is not None` after orchestrator returns, so
   both work, but construction site is clearer).

2. **Resolve via `importlib.metadata.version("harvester")`** — Same as existing log/`--version`; no second source of
   truth. PackageNotFoundError should not be swallowed silently in production images (distribution is always installed);
   tests may need the package metadata or a small helper with an injectable resolver — prefer calling `version` directly
   and relying on the installed `harvester` dist in the test env.

3. **Bump shared to ≥14.2.0** — Registry release includes the field; no git pin.

## Risks / Trade-offs

- [Shared major/minor jump 12.3 → 14.2 may pull other API changes] → Run focused harvester tests after `uv lock` / sync;
  fix breakages in-scope only if this PR introduces them.
- [Version string mismatch if log and report resolve at different times] → Negligible for a frozen install; same
  `version("harvester")` call pattern.

## Migration Plan

1. Bump dependency and lock.
2. Wire `software_version` + tests + OpenSpec.
3. No operator config change.
