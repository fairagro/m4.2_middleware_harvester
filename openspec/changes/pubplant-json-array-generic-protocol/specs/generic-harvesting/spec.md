## ADDED Requirements

### Requirement: Propagate harvest_source_id from inline JSON-LD discovery units

`JsonLdDiscoveryResult` SHALL carry an optional `harvest_source_id` (default `None`), mirroring
`UrlDiscoveryResult.harvest_source_id`, and `GenericPlugin` SHALL pass it into `MappingContext.harvest_source_id` while
`source_url` stays `None`.

#### Scenario: Protocol-supplied id reaches the mapper

- **WHEN** a Protocol yields a `JsonLdDiscoveryResult` with `harvest_source_id` set
- **THEN** the DataMapper receives it as `MappingContext.harvest_source_id`

#### Scenario: Default stays None

- **WHEN** a `JsonLdDiscoveryResult` is built without `harvest_source_id`
- **THEN** `harvest_source_id` is `None` and mapping behaviour is unchanged
