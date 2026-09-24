## MODIFIED Requirements

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
