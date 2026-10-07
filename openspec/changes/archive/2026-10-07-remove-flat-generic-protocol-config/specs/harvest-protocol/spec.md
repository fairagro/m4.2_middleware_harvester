# Spec Delta

## MODIFIED Requirements

### Requirement: Register Protocol implementations by type key

The system SHALL select Protocol implementations through a registry keyed by the active protocol type key under
`generic.protocol` (the single set type-named child such as `xml` or `mycore_solr`) and SHALL reject unregistered keys
at configuration validation. Protocol constructors SHALL receive the concrete type-specific settings model for that key
(not a structural typing.Protocol config view and not the full plugin config).

#### Scenario: Registered xml protocol resolves

- **WHEN** `generic.protocol` sets the `xml` child
- **THEN** the generic plugin constructs the XML Protocol implementation with `xml` settings

#### Scenario: Registered mycore_solr protocol resolves

- **WHEN** `generic.protocol` sets the `mycore_solr` child
- **THEN** the generic plugin constructs the MyCoRe Solr Protocol implementation with `mycore_solr` settings
