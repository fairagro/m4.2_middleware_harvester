# RDF/XML Parser

## Purpose

Shared PayloadParser in `middleware.parsing` that turns inline RDF/XML bytes or text into an `rdf_graph` ParsedPayload
for any plugin that discovers RDF/XML without a second HTTP fetch.

## ADDED Requirements

### Requirement: Provide an inline RDF/XML PayloadParser producing rdf_graph

The system SHALL provide a shared PayloadParser implementation in `middleware.parsing`, selectable by registry key
`rdf_xml` (`parser.type`), that accepts a discovery unit owned by `middleware.parsing` carrying inline RDF/XML and
returns `ParsedPayload` with `kind` `rdf_graph` and a graph value suitable for RDF `DataMapper`s. The parser MUST NOT
require an HTTP client when the RDF/XML is already present on the discovery unit.

#### Scenario: Inline RDF/XML parses to rdf_graph

- **WHEN** a discovery unit supplies well-formed RDF/XML and the RDF/XML parser is selected
- **THEN** parse succeeds with `ParsedPayload.kind == rdf_graph` and a non-empty stable identifier from the discovery
  unit

#### Scenario: HTTP client may be omitted

- **WHEN** the RDF/XML parser is invoked with inline metadata and `client` is null
- **THEN** parse does not fail solely because no HTTP client was provided

### Requirement: Fail closed on unusable RDF/XML

The system SHALL raise `ParserError` (or yield a record-level failure via the composing plugin) when the inline payload
is missing, empty, or not parseable as RDF/XML.

#### Scenario: Malformed RDF/XML fails the record

- **WHEN** the inline metadata cannot be parsed as RDF/XML
- **THEN** the parser fails with a descriptive error for that discovery unit
