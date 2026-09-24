## MODIFIED Requirements

### Requirement: Fail closed on missing required fields

The system SHALL raise a mapping error (not invent fallbacks) when:

- A `schema:Dataset` lacks a non-empty `schema:name`
- A Person contact (creator/author/contributor) would have an empty given name
- The identifier cascade yields no usable identifier

These rules define the **shared** Schema.org mapper's contract and SHALL apply to every `payload_type` that resolves to
it. The shared mapper SHALL NOT relax any of them because a single repository violates one; such relaxations belong in a
per-RDI overlay mapper registered under its own `payload_type` (see `linked-data-mapper`: "RDI-specific Schema.org
behaviour MUST live in a per-RDI mapper").

A per-RDI overlay MAY accept an additional title carrier in place of `schema:name`. It SHALL NOT relax the Person
given-name or identifier-cascade rules, SHALL NOT invent a value absent from the payload, and SHALL record the carrier
it used as provenance on the mapped ARC.

#### Scenario: Dataset without name

- **GIVEN** a `schema:Dataset` with no `schema:name` literal
- **WHEN** the shared Schema.org mapper processes the Dataset
- **THEN** a mapping error is raised indicating the missing required field

#### Scenario: Person contact without given name

- **GIVEN** a `schema:creator` that is a `schema:Person` with only `schema:familyName` "Müller"
- **WHEN** the mapper processes the contact
- **THEN** a mapping error is raised indicating the missing given name

#### Scenario: Overlay relaxation does not reach the shared mapper

- **GIVEN** a per-RDI overlay mapper that accepts `schema:headline` when `schema:name` is absent
- **WHEN** the same Dataset is processed by the shared Schema.org mapper
- **THEN** a mapping error is still raised for the missing `schema:name`
