# Principles (payload / module graph)

## Purpose

Normative module-dependency and extension-point rules for the shared `middleware.payload` package. Narrative product
overlay remains in `openspec/principles.md`.

## Requirements

### Requirement: Shared payload package owns cross-cutting mappers

The system SHALL provide a `middleware.payload` workspace package that owns intermediate-payload contracts
(`PayloadKind`, `ParsedPayload`) and shared `DataMapper` implementations (including RDF `LinkedDataMapper` /
`StableGraph`, vocabulary mappers, and the INSPIRE `inspire_general` mapper for `PayloadKind.inspire_record`). Shared
discovery-unit types and `PayloadParser` implementations SHALL live in `middleware.parsing` (not in `middleware.payload`
and not in a single protocol plugin). Protocol plugins (`inspire`, `linked_data`, `generic`, `oai_pmh`, …) MAY depend on
`middleware.payload` and `middleware.parsing`. `middleware.payload` MUST NOT depend on `middleware.parsing` or on
protocol plugin packages. The orchestrator MAY depend on `middleware.payload` for mapper config types and on
`middleware.parsing` when validating parser registries. CSW client and ISO/`MD_Metadata` parsing MAY remain in
`middleware.inspire` until a shared ISO PayloadParser exists.

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** plugins import `middleware.payload` for mapping and `middleware.parsing` for parsers/discovery units, and
  `middleware.payload` does not import those plugins or `middleware.parsing`

#### Scenario: Parsing package is the parser home

- **WHEN** a shared PayloadParser is registered
- **THEN** it is owned by `middleware.parsing` and selectable via the repository `parser.type` value without residing
  under `middleware.generic`

#### Scenario: oai_pmh does not own vocabulary mappers

- **WHEN** the OAI-PMH plugin maps records to ARC
- **THEN** it selects a shared `DataMapper` via repository `mapper.type` and does not embed vocabulary→ARC mapping in
  the plugin package

#### Scenario: oai_pmh resolves parsers from parsing

- **WHEN** an `oai_pmh` repository configures `parser.type`
- **THEN** the implementation is resolved from `middleware.parsing` without importing another protocol plugin

#### Scenario: inspire does not own ISO→ARC mapping

- **WHEN** the INSPIRE plugin maps a harvestable record to ARC
- **THEN** it selects shared `inspire_general` via repository `mapper.type` and does not embed vocabulary→ARC mapping in
  the plugin package

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

### Requirement: Extension point for new mapper types

When adding a new vocabulary→ARC mapper that reuses an existing `PayloadKind`, implementations SHALL register a new
mapper type in `middleware.payload` and expose it via repository `mapper.type`, without requiring orchestrator changes
beyond config schema registration of mapper config fields if needed.

#### Scenario: New rdf_graph mapper

- **WHEN** a new RDF vocabulary mapper is added for `PayloadKind.rdf_graph`
- **THEN** it is registered in `middleware.payload` and selectable via `mapper.type`
