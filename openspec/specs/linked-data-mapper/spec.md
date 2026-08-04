# Linked Data Mapper

## Purpose

Define the mapping contract from a parsed Linked Data RDF graph to a
`HarvestedArc` (RO-Crate JSON-LD plus study/assay composition counts).

Vocabulary-specific implementations (e.g. `GeneralSchemaOrgMapper` for
schema.org, `RegalMapper` for Regal) register against `payload_type` and
implement this interface.

## Requirements

### Requirement: LinkedDataMapper.map_graph returns HarvestedArc

The system SHALL provide a `LinkedDataMapper` ABC whose `map_graph` method
accepts an `rdflib.Graph` and returns a `HarvestedArc`. Implementations MUST
build the value via `HarvestedArc.from_arctrl` (or equivalent) so the
orchestrator receives serialized ARC JSON plus composition counts without
re-parsing RO-Crate JSON. The mapper MUST NOT return a bare JSON string.

#### Scenario: Successful map produces HarvestedArc

- **WHEN** `map_graph` is called with a mappable graph
- **THEN** the return type is `HarvestedArc`, not `str`

### Requirement: Select mapper by payload_type

The system SHALL select mapper implementations using configured `payload_type`
values via the mapper registry (explicit, non-guessing selection).

#### Scenario: Configured payload selects the registered mapper

- **WHEN** plugin config sets a supported `payload_type`
- **THEN** `LinkedDataMapper.from_config` / registry resolution returns the
  matching concrete mapper

### Requirement: Keep mapping separate from discovery

The system SHALL keep mapping logic separate from sitemap discovery and dataset
payload extraction.

#### Scenario: Mapper does not fetch sitemaps

- **WHEN** a mapper implementation runs
- **THEN** it operates only on an already-built `rdflib.Graph` and does not
  perform sitemap discovery or HTTP dataset fetch

### Requirement: Mapping failures surface as HarvesterError

Mapping failures MUST be surfaced to the orchestrator as `HarvesterError`
(typically `RecordProcessingError`) and MUST NOT crash the whole harvest run.

#### Scenario: Unmappable graph

- **WHEN** a graph lacks valid dataset metadata for the selected mapper
- **THEN** the plugin yields a `HarvesterError` for that record and continues

### Requirement: Edge case — no runtime config outside payload selection

Mapper implementations MUST NOT depend on ad-hoc runtime config outside the
fields needed for the selected `payload_type` (e.g. Regal resource base URL via
`from_config`).

#### Scenario: Payload-scoped config only

- **WHEN** a mapper is constructed from plugin config
- **THEN** only configuration relevant to that `payload_type` influences
  mapping behaviour
