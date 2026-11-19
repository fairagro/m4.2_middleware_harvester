## MODIFIED Requirements

### Requirement: InspireMapper MUST emit Investigation Comment Keywords from keyword term names

When `InspireRecord.keywords` is non-empty after parsing and validation, `InspireMapper` MUST emit Investigation keyword
Comments per the `keyword-comments` capability: per-term Comments from each retained `KeywordTerm` (label = name; term
URI = `url` when present) and the aggregate `Keywords` Comment from subject/plain names. Names MUST be trimmed; empty
names MUST be dropped. Thesaurus title MUST NOT be required to emit Comments and MUST NOT be written into Comment text
in this requirement. When `keywords` is empty, the mapper MUST NOT emit keyword Comments. `docs/mappers/inspire.md` MUST
describe aggregate + per-term Comments (including URI when present).

#### Scenario: Keyword names become one Comment

- **WHEN** a record with keyword terms named `Soil`, `soil`, and `Agriculture` is mapped
- **THEN** the Investigation MUST have Comment `Keywords` with text `Agriculture, Soil` (one representative spelling per
  casefold key; sorted)

#### Scenario: Empty keywords omit the Comment

- **WHEN** a record with an empty `keywords` list is mapped
- **THEN** the Investigation MUST NOT have a Comment named `Keywords`

#### Scenario: Per-term Comment uses URL when present

- **WHEN** a record has keyword name `Germany` with url `http://example.org/agrovoc/germany`
- **THEN** the Investigation MUST have Comment `keyword [http://example.org/agrovoc/germany]` with text `Germany`
