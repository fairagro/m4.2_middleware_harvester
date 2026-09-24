## MODIFIED Requirements

### Requirement: Shared payload package owns cross-cutting mappers

The system SHALL provide a `middleware.payload` workspace package that owns intermediate-payload contracts
(`PayloadKind`, `ParsedPayload`) and shared `DataMapper` implementations (including RDF `LinkedDataMapper` /
`StableGraph` and vocabulary mappers). Shared discovery-unit types and `PayloadParser` implementations SHALL live in
`middleware.parsing` (not in `middleware.payload` and not in a single protocol plugin). Protocol plugins (`inspire`,
`linked_data`, `generic`, `oai_pmh`, …) MAY depend on `middleware.payload` and `middleware.parsing`.
`middleware.payload` MUST NOT depend on `middleware.parsing` or on protocol plugin packages. The orchestrator MAY depend
on `middleware.payload` for mapper config types and on `middleware.parsing` when validating parser registries.

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** plugins import `middleware.payload` for mapping and `middleware.parsing` for parsers/discovery units, and
  `middleware.payload` does not import those plugins or `middleware.parsing`

#### Scenario: Parsing package is the parser home

- **WHEN** a shared PayloadParser is registered
- **THEN** it is owned by `middleware.parsing` and selectable via repository `parser.type` without residing under
  `middleware.generic`

#### Scenario: oai_pmh does not own vocabulary mappers

- **WHEN** the OAI-PMH plugin maps records to ARC
- **THEN** it selects a shared `DataMapper` via repository `mapper.type` and does not embed vocabulary→ARC mapping in
  the plugin package

#### Scenario: oai_pmh resolves parsers from parsing

- **WHEN** an `oai_pmh` repository configures `parser.type`
- **THEN** the implementation is resolved from `middleware.parsing` without importing another protocol plugin
