## Why

Remote JSON-LD `@context` handling diverges: `jsonld` rejects remotes (except a Schema.org `@vocab` stub), while
`html_jsonld` uses a hard-coded Schema.org allowlist and may still let rdflib fetch schema.org. Regal/Publisso cannot
migrate to `generic` + `jsonld` until operators can pin exactly one context URL with a process-lifetime cache (and
transitive `@import` caching). Vendoring Schema.org in-repo is out of scope (#539 closed).

## What Changes

- Add optional `parser.allowed_context_url` on `ParserConfig` (exactly one URL when set).
- Shared process-lifetime context document cache + polite HTTP fetch on cache miss, used by both `jsonld` and
  `html_jsonld`.
- When resolving a remote context, follow and cache transitive `@import` documents (not operator-configured).
- When `allowed_context_url` is set, payload remote `@context` must equal that URL exactly. When unset, absolute http(s)
  remotes are still fetched via the shared loader; `ParserConfig` warns at load (legacy configs keep working). Relative
  / non-http(s) references remain rejected.
- Remove Schema.org `@vocab` stub in `jsonld` and hard-coded Schema.org/Bioschemas allowlist gate in `html_jsonld`.
  Prefer setting `allowed_context_url` on Schema.org RDIs; omission is tolerated with a warning.
- Keep parser entry points separate; share only context policy / loader / parse helpers.
- Out of scope: Publisso YAML migration to `generic` (follow-up after this lands); TTL/ETag cache; API-shared context
  files.

## Capabilities

### New Capabilities

- `jsonld-context-loader`: Shared remote context fetch, process-lifetime cache, and rdflib document-loader contract used
  by JSON-LD PayloadParsers.

### Modified Capabilities

- `jsonld-parser`: Replace Schema.org `@vocab` exception with optional `allowed_context_url` + cached loader; HTTP
  client required whenever a remote context must be resolved.
- `payload-parser`: Document `ParserConfig.allowed_context_url` and that both `jsonld` / `html_jsonld` consume it.
- `schemaorg-to-arc-mapping`: Align harvest-time `@context` acceptance with parser `allowed_context_url` (no parallel
  hard-coded Schema.org-only gate at parse time for `html_jsonld`).
- `html-jsonld-dataset`: Note shim uses shared parser context policy (no Dataset-local allowlist).

## Impact

- Code: `middleware/parsing` (`ParserConfig`, `jsonld.py`, `html_jsonld.py`, new loader/cache helper;
  `jsonld_validation.py` allowlist usage shrinks or becomes mapper-only if still needed).
- Operator YAML: in-repo examples set `parser.allowed_context_url` where payloads use remote Schema.org IRIs; existing
  overlays without the field keep working with a warning.
- Specs/tests for both parsers; docs (`docs/linked_data_to_generic.md`).
- Unblocks later Publisso `generic` migration (#295 remnant).
