## ADDED Requirements

### Requirement: InspireMapper MUST emit Investigation Comment Keywords from keyword term names

When `InspireRecord.keywords` is non-empty after parsing and validation, `InspireMapper` MUST add exactly one
Investigation Comment named `Keywords` whose text is the comma-joined keyword **names**. Names MUST be trimmed; empty
names MUST be dropped; duplicates MUST be removed case-insensitively; remaining names MUST be sorted casefold then by
original string (same harvest-stable policy as Schema.org keyword comments). The join separator MUST be `", "`. Keyword
`url` and `thesaurus` MUST NOT be required to emit the Comment and MUST NOT be written into the Comment text in this
requirement. When `keywords` is empty, the mapper MUST NOT emit a `Keywords` Comment. This Comment is the transitional
Schema.org / Search Hub string surface; per-term keyword Comments and OntologyAnnotation keyword mapping are out of
scope. `docs/mappers/inspire.md` MUST describe this Comment mapping for keyword names and MUST document that URL /
thesaurus are retained on the record for a later ARC shape.

#### Scenario: Keyword names become one Comment

- **WHEN** a record with keyword terms named `Soil`, `soil`, and `Agriculture` is mapped
- **THEN** the Investigation MUST have Comment `Keywords` with text `Agriculture, Soil` (one representative spelling per
  casefold key; sorted)

#### Scenario: Empty keywords omit the Comment

- **WHEN** a record with an empty `keywords` list is mapped
- **THEN** the Investigation MUST NOT have a Comment named `Keywords`
