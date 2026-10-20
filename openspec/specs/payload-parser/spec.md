# Payload Parser

## Purpose

PayloadParser abstraction that turns a discovery unit into a typed ParsedPayload for shared DataMapper consumption.

## Requirements

### Requirement: Provide a PayloadParser interface with produces kind

The system SHALL provide a PayloadParser abstraction in `middleware.parsing` that exposes a class-level `produces`
`PayloadKind` and an async parse operation from a discovery unit (plus HTTP client when required) to a `ParsedPayload`.

#### Scenario: Parser advertises rdf_graph for HTML JSON-LD

- **WHEN** the HTML+JSON-LD parser is selected
- **THEN** its `produces` kind is `rdf_graph` and successful parses yield `ParsedPayload` with that kind

### Requirement: Register PayloadParser implementations by type key

The system SHALL select PayloadParser implementations through a registry in `middleware.parsing` keyed by the active
parser type from the repository sibling `parser:` block (type-as-key child name, or deprecated lifted `parser.type`) and
SHALL reject unregistered keys at configuration validation.

#### Scenario: Unknown parser.type fails closed

- **WHEN** the active parser type is not registered
- **THEN** configuration validation fails before harvesting starts

### Requirement: Keep parsers independent of Protocol discovery and DataMapper

The system SHALL keep PayloadParser implementations independent of Protocol registry/discovery orchestration and of
DataMapper mapping logic. Parsers that require HTTP SHALL accept the shared polite HTTP client type from
`middleware.harvester` and SHALL raise a descriptive error when no client is provided. Parsers that consume inline
discovery payloads MUST NOT require an HTTP client.

#### Scenario: HTTP-required parser without client fails the record

- **WHEN** a parser that needs HTTP is invoked with no client
- **THEN** parse fails with a descriptive error suitable for record-level reporting

#### Scenario: Inline parser without client succeeds when payload present

- **WHEN** an inline RDF/XML (or equivalent) parser is invoked with metadata already on the discovery unit and no client
- **THEN** parse may succeed without performing HTTP

### Requirement: Align produces with repository mapper accepts at the plugin

The system SHALL treat `parser.produces` versus repository `mapper.accepts` as a fail-fast alignment check performed by
plugins that compose shared parsers and mappers (`generic`, `oai_pmh`, and any successor), at configuration validation
and/or per record — not by inheritance between parser and mapper classes. Parser selection for those plugins SHALL use
the repository sibling `parser:` block.

#### Scenario: Alignment is by PayloadKind not class hierarchy

- **WHEN** a parser and a mapper both use `PayloadKind.rdf_graph`
- **THEN** they MAY be composed even if they do not share an inheritance edge

#### Scenario: oai_pmh uses the same kind alignment rule

- **WHEN** an `oai_pmh` repository configures sibling `parser` and `mapper` with mismatched kinds
- **THEN** validation or the harvest path fails closed before successful mapping

### Requirement: Register phenoroam_xml parser type

The system SHALL register a PayloadParser implementation under registry key `phenoroam_xml` selectable via repository
`parser` type-as-key (`parser.phenoroam_xml`) or deprecated `parser.type: phenoroam_xml`, with `produces` kind
`phenoroam_record`.

#### Scenario: phenoroam_xml produces phenoroam_record

- **WHEN** the active parser type is `phenoroam_xml`
- **THEN** the parser’s `produces` kind is `phenoroam_record`

#### Scenario: oai_pmh can compose phenoroam_xml with phenoroam_general mapper

- **WHEN** an `oai_pmh` repository sets nested `parser.phenoroam_xml` (or deprecated `parser: { type: phenoroam_xml }`)
  and nested `mapper.phenoroam_general` (or deprecated `mapper: { type: phenoroam_general }`)
- **THEN** startup kind alignment succeeds

### Requirement: ParserConfig carries optional allowed_context_url

The system SHALL expose optional `allowed_context_url` on JSON-LD parser type children under the repository sibling
`parser:` block (`parser.jsonld` / `parser.html_jsonld`), including after a deprecated `{ type: … }` lift. Both a single
http(s) IRI and a list of IRIs MUST be accepted. Matching MUST ignore trailing slashes; an `http` pin MUST also accept
the same IRI under `https` (the reverse MUST NOT hold). When unset on a JSON-LD parser type, config load MUST warn and
absolute http(s) remotes MUST still be fetched via the shared loader. Non-JSON-LD parser types MUST ignore the field.

#### Scenario: Field accepted on parser block

- **WHEN** a repository sets nested `parser.html_jsonld.allowed_context_url` (or deprecated
  `parser: { type: html_jsonld, allowed_context_url: "https://schema.org/" }`)
- **THEN** configuration validation succeeds and the Html JSON-LD parser uses that allowlisted URL

#### Scenario: List accepted on parser block

- **WHEN** a repository sets `allowed_context_url` under the active JSON-LD parser type child to a YAML list of http(s)
  IRIs
- **THEN** configuration validation succeeds and every payload remote must match one list entry

#### Scenario: Ignored by non-JSON-LD parsers

- **WHEN** a repository sets a non-JSON-LD parser type with `allowed_context_url` present on that child or via legacy
  flat fields
- **THEN** configuration validation still succeeds and that parser ignores the field

#### Scenario: Legacy flat parser.type still lifts allowed_context_url

- **WHEN** a repository sets `parser: { type: html_jsonld, allowed_context_url: "http://schema.org" }`
- **THEN** validation succeeds after lift under `parser.html_jsonld` with a deprecation warning
