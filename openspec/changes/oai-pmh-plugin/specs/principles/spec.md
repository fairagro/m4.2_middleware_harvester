## MODIFIED Requirements

### Requirement: Shared payload package owns cross-cutting mappers

The system SHALL provide a `middleware.payload` workspace package that owns intermediate-payload contracts
(`PayloadKind`, `ParsedPayload`) and shared `DataMapper` implementations (including RDF `LinkedDataMapper` /
`StableGraph` and vocabulary mappers). After the shared-parser extraction (#339), shared `PayloadParser` implementations
and discovery-unit types used across plugins SHALL live in the shared layer (not inside a single protocol plugin).
Protocol plugins (`inspire`, `linked_data`, `generic`, `oai_pmh`, …) MAY depend on `middleware.payload` (and the shared
parser surface). `middleware.payload` MUST NOT depend on protocol plugin packages. The orchestrator MAY depend on
`middleware.payload` for mapper (and parser-related) config types.

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** plugins import the shared payload/parser layer for mapping and parsing, and that layer does not import those
  plugins

#### Scenario: oai_pmh does not own vocabulary mappers

- **WHEN** the OAI-PMH plugin maps records to ARC
- **THEN** it selects a shared `DataMapper` via repository `mapper.type` and does not embed vocabulary→ARC mapping in
  the plugin package
