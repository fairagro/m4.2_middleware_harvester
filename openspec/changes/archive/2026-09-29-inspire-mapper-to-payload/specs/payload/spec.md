# Payload (delta)

## ADDED Requirements

### Requirement: Provide inspire_record PayloadKind

The system SHALL include `inspire_record` in `PayloadKind` for structured ISO-derived INSPIRE domain records (value
type: `InspireRecord` / equivalent Pydantic model owned by `middleware.payload`).

#### Scenario: inspire_record is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `inspire_record` is a valid `PayloadKind` value

### Requirement: Provide inspire_general DataMapper

The system SHALL register mapper type `inspire_general` as a `DataMapper` that accepts `PayloadKind.inspire_record`,
lives in `middleware.payload`, and maps each record to ARC per `openspec/specs/inspire-to-arc-mapping/` and
`docs/inspire_mapping.md`. The mapper MUST NOT perform CSW discovery or HTTP catalog fetches.

#### Scenario: inspire_general accepts inspire_record

- **WHEN** mapper type `inspire_general` is selected
- **THEN** the implementation accepts `PayloadKind.inspire_record` and returns `HarvestedArc` value(s) for a mappable
  record

#### Scenario: Mapper does not call CSW

- **WHEN** `inspire_general` runs
- **THEN** it operates only on an already-built `inspire_record` payload

## MODIFIED Requirements

### Requirement: Provide PayloadKind discriminator for intermediate formats

The system SHALL define a `PayloadKind` enumeration identifying supported intermediate payload formats. The enumeration
MUST include at least `rdf_graph` and `inspire_record`. Additional kinds MAY be added in later changes without changing
the discriminator mechanism.

#### Scenario: rdf_graph is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `rdf_graph` is a valid `PayloadKind` value

#### Scenario: inspire_record is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `inspire_record` is a valid `PayloadKind` value
