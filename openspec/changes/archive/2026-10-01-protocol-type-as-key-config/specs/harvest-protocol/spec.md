## MODIFIED Requirements

### Requirement: Register Protocol implementations by type key

The system SHALL select Protocol implementations through a registry keyed by the active protocol type key under
`generic.protocol` (the single set type-named child such as `xml` or `mycore_solr`) and SHALL reject unregistered keys
at configuration validation. Protocol constructors SHALL receive the concrete type-specific settings model for that key
(not a structural typing.Protocol config view and not the full plugin config).

#### Scenario: Registered xml protocol resolves

- **WHEN** `generic.protocol` sets the `xml` child (or deprecated flat config lifts to `xml`)
- **THEN** the generic plugin constructs the XML Protocol implementation with `xml` settings

#### Scenario: Registered mycore_solr protocol resolves

- **WHEN** `generic.protocol` sets the `mycore_solr` child (or deprecated flat config lifts to `mycore_solr`)
- **THEN** the generic plugin constructs the MyCoRe Solr Protocol implementation with `mycore_solr` settings

## ADDED Requirements

### Requirement: Nested protocol config separates shared and type-specific settings

The system SHALL expose a nested `protocol` configuration object on the generic plugin config. Shared transport settings
(`http`) SHALL be fields of that object. Type-specific discovery settings SHALL live under exactly one type-named child
key matching a registered Protocol type. The system SHALL NOT require a parallel `type` discriminator field beside that
child key.

#### Scenario: Shared http beside type key

- **WHEN** a generic repository configures `protocol.http` and `protocol.mycore_solr.entry_url`
- **THEN** validation succeeds and the MyCoRe Solr Protocol uses that `http` client config with the type settings

#### Scenario: Two type keys fail closed

- **WHEN** `protocol` sets both `xml` and `mycore_solr`
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Zero type keys fail closed

- **WHEN** `protocol` is present without any type-named child
- **THEN** configuration validation fails before harvesting starts
