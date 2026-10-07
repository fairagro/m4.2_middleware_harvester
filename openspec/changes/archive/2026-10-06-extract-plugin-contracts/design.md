# Design

## Context

See proposal.md for why. Today `errors.py`, `nice_http_client.py`, and `plugin_base.py` live in `middleware.harvester`.
`payload` already owns `HarvestedArc`. `harvester` depends on every plugin package; `parsing` and `oai_pmh` declaring
`harvester` is a `pyproject.toml` cycle.

## Goals / Non-Goals

**Goals:**

- Honest DAG: `contracts` ← `harvester` / `parsing` / plugins; `payload` ← `contracts` (HarvestedArc only); no plugin →
  `harvester`.
- Move types without changing harvest yield or HTTP behaviour.

**Non-Goals:**

- Isolated-install CI (#450).
- Entry-point discovery. Long-lived compatibility re-exports for plugins.

## Decisions

1. **New `middleware.contracts` package, not `payload`.** Reasoning: `payload` is source→ARC mapping; polite HTTP and
   harvest error types are plugin/runtime contracts. Putting them in `payload` would force mapper code to own HTTP
   clients. Alternative considered: `parsing` as home — INSPIRE CSW does not go through PayloadParser HTTP and would
   still need a non-parser package.

2. **Split `errors.py`.** Reasoning: `HarvesterError` / `RecordProcessingError` / `SkippedRecord` are plugin-facing;
   `format_exception_for_report` and harvest-id recovery are orchestrator/API-report helpers and stay in `harvester`.
   Alternative considered: move the whole module — would pull Middleware API report formatting into the plugin SDK.

3. **`Plugin` protocol moves with the types; `HarvestedArc` stays in `payload`.** Reasoning: the yield union is the
   plugin contract; `contracts` depending on `payload` for one type is acyclic because `payload` MUST NOT import
   `contracts`. Alternative considered: keep `plugin_base` in `harvester` — plugins would still import the orchestrator
   package for `Plugin` / `HarvestedArc` re-exports.

4. **No plugin-facing re-exports from `middleware.harvester`.** Reasoning: re-exports would leave the undeclared import
   problem in place. Alternative considered: deprecate-and-shim for one release — no published plugin wheels yet, so
   in-repo import rewrite is enough.

5. **Workspace name `contracts`, import `middleware.contracts`.** Reasoning: matches issue #155 option B2 and existing
   hatch layout (`src/middleware/<pkg>`). Alternative considered: `plugin_sdk` / `harvester_sdk` — longer, still implies
   the orchestrator package.

## Risks / Trade-offs

- [Wide import rewrite] → Mitigation: mechanical path replace plus focused pytest; no behaviour change intended.
- [`contracts` → `payload` for `Plugin`] → Mitigation: keep it the only `payload` import; do not move mappers into
  `contracts`.
- [MYPYPATH / pylint roots miss the new `src`] → Mitigation: update `.devcontainer/product.env` and root
  `pyproject.toml` members in the same change.

## Migration Plan

Single PR on `build/issue-155-extract-plugin-contracts`. Rollback is revert. No operator YAML change.

## Open Questions

None.
