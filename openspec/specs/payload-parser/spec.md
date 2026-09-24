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

The system SHALL select PayloadParser implementations through a registry in `middleware.parsing` keyed by `parser_type`
and SHALL reject unregistered keys at configuration validation.

#### Scenario: Unknown parser_type fails closed

- **WHEN** `parser_type` is not registered
- **THEN** configuration validation fails before harvesting starts

### Requirement: Keep parsers independent of Protocol discovery and DataMapper

The system SHALL keep PayloadParser implementations independent of Protocol registry/discovery orchestration and of
DataMapper mapping logic. Parsers that require HTTP SHALL accept the shared polite HTTP client type from
`middleware.harvester` and SHALL raise a descriptive error when no client is provided. Parsers that consume inline
discovery payloads MUST NOT require an HTTP client.

#### Scenario: HTTP-required parser without client fails the record

- **WHEN** a parser that needs HTTP is invoked with no client
- **THEN** parse fails with a descriptive error suitable for record-level reporting

### Requirement: Align produces with repository mapper accepts at the plugin

The system SHALL treat `parser.produces` versus repository `mapper.accepts` as a fail-fast alignment check performed by
plugins that compose shared parsers and mappers (including `generic`), at configuration validation and/or per record —
not by inheritance between parser and mapper classes.

#### Scenario: Alignment is by PayloadKind not class hierarchy

- **WHEN** a parser and a mapper both use `PayloadKind.rdf_graph`
- **THEN** they MAY be composed even if they do not share an inheritance edge
