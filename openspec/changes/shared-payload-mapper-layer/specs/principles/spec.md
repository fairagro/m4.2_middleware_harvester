## ADDED Requirements

### Requirement: Shared payload package owns cross-cutting mappers

The system SHALL provide a `middleware.payload` workspace package that owns
intermediate-payload contracts (`PayloadKind`, `ParsedPayload`) and shared
`DataMapper` implementations. Protocol plugins MAY depend on
`middleware.payload`. `middleware.payload` MUST NOT depend on protocol plugin
packages (`inspire`, `linked_data`, future OAI, …). The orchestrator MAY
depend on `middleware.payload` for mapper config types.

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** plugins import `middleware.payload` for mapping, and
  `middleware.payload` does not import those plugins

### Requirement: Extension point for new mapper types

When adding a new vocabulary→ARC mapper that reuses an existing
`PayloadKind`, implementations SHALL register a new mapper type in
`middleware.payload` and expose it via repository `mapper.type`, without
requiring orchestrator changes beyond config schema registration of mapper
config fields if needed.

#### Scenario: New rdf_graph mapper

- **WHEN** a new RDF vocabulary mapper is added for `PayloadKind.rdf_graph`
- **THEN** it is registered in `middleware.payload` and selectable via
  `mapper.type`
