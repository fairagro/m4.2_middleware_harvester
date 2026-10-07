# Spec Delta

## ADDED Requirements

### Requirement: Leaf contracts package owns plugin-facing harvest types

The system SHALL provide a `middleware.contracts` workspace package that owns the plugin-facing harvest types
`HarvesterError`, `RecordProcessingError`, `SkippedRecord`, `NiceHttpClient` / `NiceHttpClientConfig`, and the `Plugin`
protocol. Protocol plugins and `middleware.parsing` MUST depend on `middleware.contracts` for those types and MUST NOT
import `middleware.harvester`. `middleware.contracts` MUST NOT depend on `middleware.harvester`, `middleware.parsing`,
or protocol plugin packages. `middleware.contracts` MAY depend on `middleware.payload` only for `HarvestedArc` on the
`Plugin` yield union. `middleware.payload` MUST NOT depend on `middleware.contracts`.

#### Scenario: Plugins do not import the orchestrator package

- **WHEN** a protocol plugin needs `HarvesterError`, `SkippedRecord`, `NiceHttpClient`, or `Plugin`
- **THEN** it imports them from `middleware.contracts` and has no `middleware.harvester` import

#### Scenario: Contracts package stays a leaf under the orchestrator

- **WHEN** module dependencies are reviewed
- **THEN** `contracts` does not import `harvester`, `parsing`, or protocol plugins
