## Purpose

Defines the shared Investigation Comment contract for keyword and optional classification terms across all
keyword-producing mappers, including aggregate `Keywords` transitional export and unique per-term Comment names.

## ADDED Requirements

### Requirement: Mappers MUST emit unique per-term keyword Comments

When a mapper has one or more subject/plain keyword terms after harvest validation, it MUST append one Investigation
Comment per retained term. The Comment **name** MUST be `keyword [<term-URI>]` when the term has a non-empty URI,
otherwise `keyword [<label>]` using the trimmed label. The Comment **text** MUST be the trimmed label. Bare Comment name
`keyword` without brackets MUST NOT be used. Comment names within the Investigation MUST be unique; when two terms would
collide after the naming rules, the mapper MUST keep a single Comment using the same harvest-stable dedupe policy as the
aggregate (casefold). Empty labels MUST be omitted.

#### Scenario: Plain string becomes keyword [label]

- **WHEN** a record has a single plain keyword label `Soil` with no URI
- **THEN** the Investigation MUST have Comment name `keyword [Soil]` with text `Soil`

#### Scenario: URI term uses keyword [URI]

- **WHEN** a record has keyword label `aerosols` with URI `http://example.org/agrovoc/c_1`
- **THEN** the Investigation MUST have Comment name `keyword [http://example.org/agrovoc/c_1]` with text `aerosols`

### Requirement: Optional DDC Comments MUST require a class URI

When a classification/DDC term is known **with** a non-empty class URI, the mapper MUST append Comment name
`keyword [DDC:<class-URI>]` with text equal to the classification label. When no class URI is present, the mapper MUST
NOT emit a DDC Comment for that term. Absence of DDC MUST NOT drop subject/plain Comments.

#### Scenario: DDC with URI

- **WHEN** a record has DDC label `Landwirtschaft` with URI `http://dewey.info/class/630/`
- **THEN** the Investigation MUST have Comment `keyword [DDC:http://dewey.info/class/630/]` with that label

#### Scenario: DDC without URI omitted

- **WHEN** a classification label is present without a class URI
- **THEN** the Investigation MUST NOT have a `keyword [DDC:…]` Comment for that label

### Requirement: Aggregate Keywords Comment remains for subject labels only

When at least one subject/plain label is retained, the mapper MUST also append exactly one Investigation Comment named
`Keywords` whose text is the comma-joined subject/plain labels after trim, empty-drop, casefold-dedupe, and sort
(casefold then original string). The join separator MUST be `", "`. DDC/classification labels MUST NOT appear in that
aggregate. When no subject/plain labels remain, the mapper MUST NOT emit `Keywords`.

#### Scenario: Aggregate excludes DDC

- **WHEN** a record has subject labels `Soil`, `Water` and a DDC label `Landwirtschaft`
- **THEN** Comment `Keywords` MUST be `Soil, Water` (order per sort policy) and MUST NOT include `Landwirtschaft`
