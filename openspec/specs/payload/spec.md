# Payload

## Purpose

Shared intermediate-payload contracts and `DataMapper` registry for mapping harvested records to ARC without tying
vocabulary mappers to a single protocol plugin.

## Requirements

### Requirement: Provide PayloadKind discriminator for intermediate formats

The system SHALL define a `PayloadKind` enumeration identifying supported intermediate payload formats. The enumeration
MUST include at least `rdf_graph` and `inspire_record`. Additional kinds MAY be added in later changes without changing
the discriminator mechanism.

#### Scenario: rdf_graph is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `rdf_graph` is a valid `PayloadKind` value

### Requirement: Provide inspire_record PayloadKind

The system SHALL include `inspire_record` in `PayloadKind` for structured ISO-derived INSPIRE domain records (value
type: `InspireRecord` / equivalent Pydantic model owned by `middleware.payload`).

#### Scenario: inspire_record is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `inspire_record` is a valid `PayloadKind` value

### Requirement: Provide inspire_general DataMapper

The system SHALL register mapper type `inspire_general` as a `DataMapper` that accepts `PayloadKind.inspire_record`,
lives in `middleware.payload`, and maps each record to ARC per `openspec/specs/inspire-to-arc-mapping/` and
`docs/mappers/inspire.md`. The mapper MUST NOT perform CSW discovery or HTTP catalog fetches.

#### Scenario: inspire_general accepts inspire_record

- **WHEN** mapper type `inspire_general` is selected
- **THEN** the implementation accepts `PayloadKind.inspire_record` and returns `HarvestedArc` value(s) for a mappable
  record

#### Scenario: Mapper does not call CSW

- **WHEN** `inspire_general` runs
- **THEN** it operates only on an already-built `inspire_record` payload

### Requirement: Provide ParsedPayload envelope

The system SHALL provide a `ParsedPayload` (or equivalent) envelope that carries at least: `kind` (`PayloadKind`), a
typed `value`, and a stable `identifier` for error reporting. Producers of intermediate payloads MUST emit this envelope
(or an equivalent that exposes the same fields) before mapping when using the shared DataMapper API.

#### Scenario: Envelope exposes kind and identifier

- **WHEN** a dataset/parser produces an intermediate payload for mapping
- **THEN** the envelope exposes `kind` and a non-empty stable `identifier`

### Requirement: Provide DataMapper ABC and registry

The system SHALL provide a `DataMapper` abstraction that maps an intermediate payload to `HarvestedArc`, selected via an
explicit registry key (mapper type). Each registered mapper MUST declare the `PayloadKind` it accepts. The mapper MUST
NOT perform protocol discovery or HTTP fetching of source catalogs.

#### Scenario: Registry selects mapper by configured type

- **WHEN** repository config sets a supported mapper type
- **THEN** registry resolution returns the matching `DataMapper` implementation

#### Scenario: Mapper does not discover sources

- **WHEN** a `DataMapper` runs
- **THEN** it operates only on an already-built intermediate payload and does not perform sitemap/CSW/OAI discovery

### Requirement: LinkedDataMapper refines DataMapper for rdf_graph

The system SHALL provide a `LinkedDataMapper` refinement of `DataMapper` for `PayloadKind.rdf_graph`. Concrete
vocabulary mappers (Schema.org general, Regal) MUST live in `middleware.payload`, register in the shared registry, and
accept `rdf_graph`. Behavioural ARC field rules remain those of `openspec/specs/linked-data-mapper/` and
`docs/mappers/regal.md` as applicable (including StableGraph / ResourceView requirements).

#### Scenario: Schema.org mapper accepts rdf_graph

- **WHEN** mapper type `schema_org_general` is selected
- **THEN** the implementation accepts `PayloadKind.rdf_graph` and returns `HarvestedArc` for a mappable graph

### Requirement: Fail fast on PayloadKind mismatch

The system SHALL reject at configuration validation (or immediately before mapping, fail-fast) any combination where the
producer/parser `produces` kind differs from the selected mapper `accepts` kind.

#### Scenario: Incompatible kind aborts or fails closed

- **WHEN** config pairs a producer of kind A with a mapper that accepts kind B (A ≠ B)
- **THEN** startup validation fails with a clear error, or the harvest path fails closed before invoking the mapper

### Requirement: Support PayloadKind phenoroam_record

The system SHALL extend `PayloadKind` with `phenoroam_record` for typed PhenoRoam intermediate records produced by the
`phenoroam_xml` parser and accepted by the `phenoroam_general` DataMapper.

#### Scenario: phenoroam_general mapper accepts phenoroam_record

- **WHEN** the active mapper type is `phenoroam_general`
- **THEN** the mapper’s `accepts` kind is `phenoroam_record`

### Requirement: Register phenoroam_general mapper type

The system SHALL register a DataMapper implementation under registry key `phenoroam_general` selectable via repository
`mapper` type-as-key (`mapper.phenoroam_general`) or deprecated `mapper.type: phenoroam_general`.

#### Scenario: Unknown mapper type still fails closed

- **WHEN** the active mapper type is not registered
- **THEN** configuration validation fails before harvest

### Requirement: Harvested ARCs MUST have unique Comment names

`HarvestedArc.from_arctrl` MUST merge Comments with the same name on the Investigation, each Study, each Assay, each
Person (Investigation and Study contacts, Assay performers) and each Publication into the first such Comment, with the
distinct non-empty values joined by `; ` in order. The serialized RO-Crate MUST keep the root `dateModified` and MUST
NOT contain the `dateModified` Comment node or references to it. Reading the RO-Crate with
`ARC.from_rocrate_json_string` and writing it with `ARC.Write` MUST succeed.

#### Scenario: Repeated Regal facet

- **WHEN** an Investigation has Comments `associatedDataset` "frl:1" and `associatedDataset` "frl:2"
- **THEN** it MUST have one Comment `associatedDataset` "frl:1; frl:2"

#### Scenario: API read and write

- **WHEN** a harvested ARC with repeated Comment names and a `dateModified` is read back and written with `ARC.Write`
- **THEN** the write MUST succeed and the Investigation MUST have exactly one `dateModified` Comment
