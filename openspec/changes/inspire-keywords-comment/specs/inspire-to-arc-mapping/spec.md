## ADDED Requirements

### Requirement: InspireMapper MUST emit Investigation Comment Keywords from record.keywords

When `InspireRecord.keywords` is non-empty after parsing and validation, `InspireMapper` MUST add exactly one
Investigation Comment named `Keywords` whose text is the comma-joined keyword labels. Labels MUST be trimmed; empty
labels MUST be dropped; duplicates MUST be removed case-insensitively; remaining labels MUST be sorted casefold then by
original string (same harvest-stable policy as Schema.org keyword comments). The join separator MUST be `", "`. When
`keywords` is empty, the mapper MUST NOT emit a `Keywords` Comment. This Comment is the transitional Schema.org / Search
Hub string surface; per-term keyword Comments and OntologyAnnotation keyword mapping are out of scope for this
requirement. `docs/mappers/inspire.md` MUST describe this Comment mapping for MD_Keywords (not “Not mapped”).

#### Scenario: Keywords present become one Comment

- **WHEN** a record with keywords `["Soil", "soil", " Agriculture "]` is mapped
- **THEN** the Investigation MUST have Comment `Keywords` with text `Agriculture, Soil` (one representative spelling per
  casefold key; sorted)

#### Scenario: Empty keywords omit the Comment

- **WHEN** a record with an empty `keywords` list is mapped
- **THEN** the Investigation MUST NOT have a Comment named `Keywords`
