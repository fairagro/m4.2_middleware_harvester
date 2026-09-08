## Purpose

Defines the shared intermediate-payload contracts and DataMapper registry in
`middleware.payload`, so protocol plugins can reuse record→ARC mapping without
owning vocabulary-specific mappers.

## ADDED Requirements

### Requirement: Provide PayloadKind discriminator for intermediate formats

The system SHALL define a `PayloadKind` enumeration identifying supported
intermediate payload formats. v1 MUST include `rdf_graph` (value type:
RDF graph). Additional kinds MAY be added in later changes without changing
the Discriminator mechanism.

#### Scenario: rdf_graph is available

- **WHEN** a producer or mapper declares its kind
- **THEN** `rdf_graph` is a valid `PayloadKind` value

### Requirement: Provide ParsedPayload envelope

The system SHALL provide a `ParsedPayload` (or equivalent) envelope that
carries at least: `kind` (`PayloadKind`), a typed `value`, and a stable
`identifier` for error reporting. Producers of intermediate payloads MUST
emit this envelope (or an equivalent that exposes the same fields) before
mapping.

#### Scenario: Envelope exposes kind and identifier

- **WHEN** a dataset/parser produces an intermediate payload for mapping
- **THEN** the envelope exposes `kind` and a non-empty stable `identifier`

### Requirement: Provide DataMapper ABC and registry

The system SHALL provide a `DataMapper` abstraction that maps an intermediate
payload to `HarvestedArc`, selected via an explicit registry key (mapper type).
Each registered mapper MUST declare the `PayloadKind` it accepts. The mapper
MUST NOT perform protocol discovery or HTTP fetching of source catalogs.

#### Scenario: Registry selects mapper by configured type

- **WHEN** repository config sets a supported mapper type
- **THEN** registry resolution returns the matching `DataMapper` implementation

#### Scenario: Mapper does not discover sources

- **WHEN** a `DataMapper` runs
- **THEN** it operates only on an already-built intermediate payload and does
  not perform sitemap/CSW/OAI discovery

### Requirement: LinkedDataMapper refines DataMapper for rdf_graph

The system SHALL provide a `LinkedDataMapper` refinement of `DataMapper` for
`PayloadKind.rdf_graph`. Concrete vocabulary mappers (Schema.org general,
Regal) MUST register in the shared payload package and accept `rdf_graph`.
Behavioural ARC field rules remain those of
`openspec/specs/linked-data-mapper/` and `docs/regal_mapping.md` as applicable.

#### Scenario: Schema.org mapper accepts rdf_graph

- **WHEN** mapper type `schema_org_general` is selected
- **THEN** the implementation accepts `PayloadKind.rdf_graph` and returns
  `HarvestedArc` for a mappable graph

### Requirement: Fail fast on PayloadKind mismatch

The system SHALL reject at configuration validation (or immediately before
mapping, fail-fast) any combination where the producer/parser `produces` kind
differs from the selected mapper `accepts` kind.

#### Scenario: Incompatible kind aborts or fails closed

- **WHEN** config pairs a producer of kind A with a mapper that accepts kind B
  (A ≠ B)
- **THEN** startup validation fails with a clear error, or the harvest path
  fails closed before invoking the mapper
