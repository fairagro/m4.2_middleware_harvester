## MODIFIED Requirements

### Requirement: Validate @context before mapping

The system SHALL ensure harvest-time acceptance of remote JSON-LD `@context` IRIs for Schema.org HTML/`jsonld` sources
is governed by `parser.allowed_context_url` and the shared context loader (not a hard-coded Schema.org-only parse-time
allowlist). Mapper-side vocabulary expectations for Schema.org graphs MAY remain, but MUST NOT reintroduce a second
hard-coded remote-context allowlist that rejects an IRI already accepted by the parser for that repository. `@import`
and nested remote `@context` loads discovered while resolving a root MUST be absolute `http(s)` IRIs resolved through
the shared loader cache. Relative imports remain rejected.

#### Scenario: Standard Schema.org HTTPS context

- **GIVEN** a JSON-LD payload with `"@context": "https://schema.org/"` and
  `parser.allowed_context_url: "https://schema.org/"`
- **WHEN** the record is harvested through `html_jsonld` or `jsonld`
- **THEN** context resolution uses the shared loader and mapping may proceed on the resulting graph

#### Scenario: Standard Schema.org HTTP context

- **GIVEN** a JSON-LD payload with `"@context": "http://schema.org/"` and
  `parser.allowed_context_url: "http://schema.org/"`
- **WHEN** the record is harvested through `html_jsonld` or `jsonld`
- **THEN** context resolution uses the shared loader and mapping may proceed on the resulting graph

#### Scenario: Mixed http/https in same graph

- **GIVEN** payloads that use different Schema.org IRI variants across records
- **WHEN** each repository sets `allowed_context_url` to the exact IRI used by that source
- **THEN** each record resolves under its configured URL (exact match; no cross-variant aliasing required)

#### Scenario: Known extension context (Bioschemas)

- **GIVEN** a remote Bioschemas context IRI appears only via `@import` from the allowlisted root context document
- **WHEN** the root `allowed_context_url` is fetched and imports are cached
- **THEN** parse succeeds without requiring a second operator-configured URL for Bioschemas

#### Scenario: Unknown context when pinned

- **GIVEN** `parser.allowed_context_url` is set and a payload `@context` URL that does not equal it
- **WHEN** parse runs
- **THEN** the record fails closed at the parser (no mapping)

#### Scenario: Unset pin still resolves remote context

- **GIVEN** `parser.allowed_context_url` is unset and the payload `@context` is an absolute http(s) Schema.org IRI
- **WHEN** parse runs with a polite HTTP client
- **THEN** context resolution uses the shared loader and mapping may proceed on the resulting graph

#### Scenario: Relative @import rejected

- **GIVEN** a context document (payload or fetched root) contains a relative `@import`
- **WHEN** context resolution runs
- **THEN** resolution fails closed (relative imports are rejected)

#### Scenario: Parser allowlisted Schema.org context reaches mapping

- **GIVEN** a repository with `parser.allowed_context_url` set to the payload's Schema.org context IRI
- **WHEN** the payload parses to an `rdf_graph` and is passed to the Schema.org mapper
- **THEN** mapping is not rejected solely because the context IRI is absent from a hard-coded module allowlist

#### Scenario: Standard Schema.org HTTPS context with configured URL

- **GIVEN** a JSON-LD payload with `"@context": "https://schema.org/"` and `allowed_context_url: "https://schema.org/"`
- **WHEN** the record is harvested through `html_jsonld` or `jsonld`
- **THEN** context resolution uses the shared loader and mapping may proceed on the resulting graph
