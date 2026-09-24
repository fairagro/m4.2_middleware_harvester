# Proposal

## Why

`PayloadParser`, `ParserType`, and `DiscoveryResult` live under `middleware.generic`, so any non-generic plugin that
needs shared parsers (notably the upcoming OAI-PMH plugin,
[#142](https://github.com/fairagro/m4.2_middleware_harvester/issues/142)) would have to import another protocol plugin
or duplicate the parser stack. Mappers already live in a shared package; parsers should too. Tracked as
[#339](https://github.com/fairagro/m4.2_middleware_harvester/issues/339).

Explore lock-in: **Option B** — new sibling workspace package `middleware.parsing` that MAY depend on `harvester`
(`NiceHttpClient`, `HarvesterError`) and `payload`, keeping concrete parser signatures close to today without structural
HTTP Protocols or error-wrapping in `payload`.

## What Changes

- Add workspace package `middleware/parsing` owning: `DiscoveryResult` hierarchy, `ParserType`, `PayloadParser` ABC +
  registry, concrete parsers (starting with `html_jsonld`), parser-local errors that remain `HarvesterError` subclasses.
- **BREAKING (import paths):** Move those symbols out of `middleware.generic`; update `generic`, `linked_data`, and
  `harvester` config imports. Temporary re-exports MAY exist only if needed for a short coexistence window; prefer
  updating call sites in the same change.
- **BREAKING (config):** Lift shared parser selection to repository sibling `parser: { type: ... }` (like `mapper:`). Do
  not keep `generic.parser_type` (plugin unused in production; hard cut).
- `middleware.generic` retains Protocol registry, generic pipeline, and plugin orchestration; it **consumes** shared
  parsers.
- `linked_data` stops importing discovery/parsers from `generic` for those concerns (Protocol/sitemap shims to generic
  may remain where still required for unmigrated sources).
- Update `.importlinter`, `openspec/principles.md`, MYPYPATH / workspace / quality overlays for the new package.
- OpenSpec deltas below. Behaviour of HTML+JSON-LD parsing and generic harvest composition MUST remain observationally
  equivalent.

## Capabilities

### New Capabilities

- `shared-parsing`: Ownership and dependency rules for the `middleware.parsing` package (shared discovery units +
  PayloadParser registry across protocol plugins).

### Modified Capabilities

- `payload-parser`: Parsers and discovery units are provided by `middleware.parsing`, not by a single protocol plugin;
  HTTP-required parsers may use `NiceHttpClient` directly.
- `principles`: Module graph — `parsing` between plugins and payload; `parsing` MAY import `harvester` + `payload`;
  plugins MAY import `parsing`; `payload` MUST NOT import `parsing` or plugins; plugins MUST NOT import each other for
  parsers.
- `generic-harvesting`: Generic plugin consumes shared parser registry from `middleware.parsing`; config no longer
  requires `parser_type` on the plugin block.
- `harvester-configuration`: Repository sibling `parser:` block (required for `generic`).
- `harvest-protocol`: Discovery unit types are shared via `middleware.parsing` (Protocols still live in generic /
  linked_data as today).

## Impact

- New package under `middleware/parsing`; root `pyproject.toml`, `.devcontainer/product.env`, import-linter,
  AGENTS/quality path lists.
- Call-site churn in `middleware/generic`, `middleware/linked_data`, `middleware/harvester` (config validation).
- Enables #142 without `oai_pmh → generic` for parsers.
- Does **not** add RDF/XML parser or OAI plugin (those stay on #142).

## Non-goals

- Moving parsers into `middleware.payload` (Option A — rejected).
- OAI-PMH plugin, RDF/XML parser, EPrints mapper.
- Deleting `linked_data` or finishing all generic migrations (#293–#296).
- Changing HTML+JSON-LD parse semantics or `PayloadKind` contracts.
