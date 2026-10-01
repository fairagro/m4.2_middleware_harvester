## Why

Remote JSON-LD `@context` handling diverges: `jsonld` rejects remotes (except a Schema.org `@vocab` stub), while
`html_jsonld` uses a hard-coded Schema.org allowlist and may still let rdflib fetch schema.org. Regal/Publisso cannot
migrate to `generic` + `jsonld` until operators can allow exactly one context URL with a process-lifetime cache (and
transitive `@import` caching). Vendoring Schema.org in-repo is out of scope (#539 closed).

## What Changes

- Add optional `parser.allowed_context_url` on `ParserConfig` (exactly one URL when set).
- Shared process-lifetime context document cache + polite HTTP fetch on cache miss, used by both `jsonld` and
  `html_jsonld`.
- When resolving the allowlisted root context, follow and cache transitive `@import` documents (not
  operator-configured).
- Payload remote `@context` must equal the configured URL (string or sole remote entry in a list); unset → reject remote
  IRIs on the payload (DCAT expanded / no-context stays valid).
- **BREAKING (operator config):** remove Schema.org `@vocab` stub in `jsonld`; remove hard-coded Schema.org/Bioschemas
  allowlist gate in `html_jsonld`. Schema.org RDIs must set `allowed_context_url` to the IRI present in their payloads.
- Keep parser entry points separate; share only context policy / loader / parse helpers.
- Out of scope: Publisso YAML migration to `generic` (follow-up after this lands); TTL/ETag cache; API-shared context
  files.

## Capabilities

### New Capabilities

- `jsonld-context-loader`: Shared allowlisted remote context fetch, process-lifetime cache, and rdflib document-loader
  contract used by JSON-LD PayloadParsers.

### Modified Capabilities

- `jsonld-parser`: Replace Schema.org `@vocab` exception with optional `allowed_context_url` + cached loader; HTTP
  client required when a remote allowlisted context must be resolved.
- `payload-parser`: Document `ParserConfig.allowed_context_url` and that both `jsonld` / `html_jsonld` consume it.
- `schemaorg-to-arc-mapping`: Align harvest-time `@context` acceptance with parser `allowed_context_url` (no parallel
  hard-coded Schema.org-only gate at parse time for `html_jsonld`).
- `html-jsonld-dataset`: Note shim uses shared parser context policy (no Dataset-local allowlist).

## Impact

- Code: `middleware/parsing` (`ParserConfig`, `jsonld.py`, `html_jsonld.py`, new loader/cache helper;
  `jsonld_validation.py` allowlist usage shrinks or becomes mapper-only if still needed).
- Operator YAML: e!DAL / OpenAgrar / PlabiPD examples need `parser.allowed_context_url` where payloads use remote
  Schema.org IRIs.
- Specs/tests for both parsers; docs (`docs/linked_data_to_generic.md` note that Regal waits on this).
- Unblocks later Publisso `generic` migration (#295 remnant).
