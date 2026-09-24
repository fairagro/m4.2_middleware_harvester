## MODIFIED Requirements

### Requirement: Provide a Protocol interface for discovery

The system SHALL provide a Protocol abstraction that, given plugin configuration and an HTTP client where needed, can
stream discovery units and optionally report an expected count. Successful discovery units SHALL expose a stable
`identifier` used for deduplication. The discovery-unit type hierarchy used across plugins SHALL be defined in
`middleware.parsing` so Protocol implementations and PayloadParsers share the same types without cross-plugin imports.

#### Scenario: Discovery yields identifiable units

- **WHEN** a Protocol discovers harvestable units
- **THEN** each successful unit exposes a stable `identifier`

#### Scenario: Shared discovery types

- **WHEN** a Protocol yields a URL or inline discovery unit
- **THEN** the unit is an instance of a discovery type owned by `middleware.parsing`
