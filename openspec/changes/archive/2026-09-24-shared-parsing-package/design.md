# Design

## Context

See `proposal.md`. Explore lock-in for [#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339):
**Option B** — sibling package `middleware.parsing`, not moving parsers into `middleware.payload`.

Today `middleware.generic` owns discovery types + parsers; `linked_data` re-exports/imports them from generic;
`harvester.config` imports `PayloadParser` from generic for kind checks. `payload ↛ harvester` forbids putting
`NiceHttpClient`-typed parsers into `payload` without Protocols/wrapping (Option A — rejected).

## Goals / Non-Goals

**Goals:**

- One import home for shared parsers/discovery units usable by `generic`, `linked_data`, and future `oai_pmh`.
- Keep `parse(..., client: NiceHttpClient | None)` and `HarvesterError` subclasses without payload contamination.
- Observational parity for existing html_jsonld + generic harvest tests.

**Non-Goals:**

- New parser kinds (RDF/XML → #142).
- Moving `Protocol` ABC out of generic.
- Ending `linked_data` coexistence.

## Decisions

### 1. Package name `middleware.parsing`

**Why:** Clear sibling to `payload` (mappers) vs `parsing` (discovery→ParsedPayload). Avoids overloading `payload` with
HTTP/harvester deps.

**Alternatives:** `middleware.payload` (A), keep in generic (status quo).

### 2. Dependencies: `parsing → harvester + payload`

**Why:** Direct `NiceHttpClient` and `ParserError(HarvesterError)` — no structural HTTP Protocol, no wrap layer.

**Constraint:** import-linter must allow `parsing → harvester` while forbidding `payload → parsing` and
`parsing → {inspire,linked_data,generic,...}`.

### 3. Move in one PR: types + html_jsonld + call sites

**Why:** Avoid long-lived dual homes. Prefer updating imports over permanent re-exports from `generic.discovery`.

**Optional:** thin deprecated re-exports in `generic` only if needed for in-flight branches — default is delete + fix.

### 4. `ParserType` / `ParserConfig` live in `parsing`; `ProtocolType` stays in `generic.config`

**Why:** Protocol registry remains generic-owned; parser keys are shared. Repository sibling `parser: { type }` mirrors
`mapper: { type }` so future plugins (OAI) select parsers without nesting under `generic:`.

Generic plugin config does not carry `parser_type`; operators set sibling `parser: { type }` only.

### 5. Errors: `middleware.parsing.errors.ParserError(HarvesterError)`

**Why:** Replace `GenericParserError` for shared parsers; `generic` may keep `GenericProtocolError` for protocol-only
failures. Map/wrap at boundaries only if an old name must remain temporarily.

### 6. Registration: `register_builtin_parsers` side-effect module in `parsing`

**Why:** Same pattern as `payload` mapper builtins; plugins import the gate explicitly.

## Risks / Trade-offs

| Risk                                                    | Mitigation                                                                                                                                                                |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New package wiring misses MYPYPATH/pylint/import-linter | Checklist in tasks; run quality scripts                                                                                                                                   |
| `parsing → harvester` widens harvester surface          | Limit imports to `NiceHttpClient` + error bases; no orchestrator                                                                                                          |
| Circular `harvester → parsing → harvester`              | `parsing` imports only `nice_http_client` / `errors`; harvester config imports parsing registry — ensure no cycle via plugin packages (harvester already imports plugins) |
| linked_data still needs generic for Protocol shims      | Document allowed remaining edges; remove parser edges                                                                                                                     |

**Cycle note:** `harvester.config` already imports `PayloadParser` and plugins. `parsing → harvester.errors` /
`nice_http_client` must not import `harvester.config` or plugins. Keep that boundary in code review.

## Migration Plan

1. Add empty `middleware/parsing` package + deps.
2. Move modules; fix imports; run unit tests.
3. Update principles + import-linter; validate OpenSpec.
4. Merge before #142 apply.

Rollback: revert the PR; no data migration.

## Open Questions

- None that block specs/tasks; exact module layout (`parsing/discovery.py`, `parsing/parser/…`) left to implementer
  mirroring current generic layout.
