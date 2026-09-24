## ADDED Requirements

### Requirement: OpenAgrar overlay builds on the shared Schema.org mapper

The system SHALL provide `OpenAgrarSchemaOrgMapper` as a subclass of `GeneralSchemaOrgMapper`, registered in the overlay
registry under the name `openagrar` and declaring `schema_org_general` as the payload format it builds on. It SHALL
override only the title-fallback hook and SHALL inherit every other Schema.org rule unchanged — identifier cascade,
contacts, publisher policy, comments, ordering, and fail-closed behaviour all come from the shared mapper and are
defined in `schemaorg-to-arc-mapping` and `linked-data-mapper`.

This spec is an overlay: it states only the deltas relative to `schemaorg-to-arc-mapping` and SHALL NOT restate base
mapping rules.

#### Scenario: OpenAgrar mapper key selects the overlay mapper

- **WHEN** plugin config sets `payload_type: schema_org_general` and `mapper: openagrar`
- **THEN** overlay registry resolution MUST return `OpenAgrarSchemaOrgMapper`

#### Scenario: OpenAgrar config without the mapper key uses the shared mapper

- **WHEN** an OpenAgrar repository config omits `mapper`
- **THEN** the shared `GeneralSchemaOrgMapper` MUST be constructed, and records lacking `schema:name` MUST fail closed
  as record-level errors rather than mapping with an invented title

#### Scenario: Records with schema:name map identically to the shared mapper

- **WHEN** a Schema.org Dataset with a non-empty `schema:name` is mapped by both `OpenAgrarSchemaOrgMapper` and
  `GeneralSchemaOrgMapper` with the same `MappingContext`
- **THEN** both MUST produce the same Investigation identifier and title, and neither MUST record a `Title Source`
  comment

### Requirement: OpenAgrar accepts alternative title carriers when schema:name is absent

OpenAgrar's MyCoRe export omits `schema:name` on a small share of otherwise valid records while still exposing a usable
title elsewhere. When `schema:name` is missing or blank after trim, `OpenAgrarSchemaOrgMapper` SHALL resolve the Dataset
title from the first carrier that yields a non-empty value, in this order:

1. `schema:headline`
2. the first non-empty `schema:alternativeHeadline`, in the access layer's stable order
3. the page-title hint carried on `MappingContext.html_title` (supplied by `html_jsonld` datasets from `citation_title`
   meta, else `<title>`)

When none of these yields a non-empty value, mapping SHALL fail closed with the shared mapper's error (no
`HarvestedArc`, no `Untitled` display title). The mapper SHALL declare exactly these carriers, plus `schema:name`, so
the fail-closed error names what was actually tried.

#### Scenario: Headline is preferred over alternativeHeadline

- **GIVEN** a Dataset with blank `schema:name`, `schema:headline` "Flower visitors in legume-intercrops", and a
  non-empty `schema:alternativeHeadline`
- **WHEN** `OpenAgrarSchemaOrgMapper` maps the Dataset
- **THEN** the Investigation title MUST be "Flower visitors in legume-intercrops"

#### Scenario: First non-empty alternativeHeadline wins

- **GIVEN** a Dataset with no `schema:name` or `schema:headline` and `schema:alternativeHeadline` values
  `["", "Flower visitors in legume-intercrops", "Ignored second entry"]`
- **WHEN** the mapper resolves the title
- **THEN** the Investigation title MUST be "Flower visitors in legume-intercrops"

#### Scenario: HTML page title is the last resort

- **GIVEN** a Dataset with no `schema:name`, `schema:headline`, or `schema:alternativeHeadline`, mapped with
  `MappingContext.html_title` set
- **WHEN** the mapper resolves the title
- **THEN** the Investigation title MUST be that page-title hint

#### Scenario: No carrier available fails closed

- **GIVEN** a Dataset with none of the four carriers populated
- **WHEN** the mapper maps the Dataset
- **THEN** a mapping error MUST be raised naming `schema:name`, `schema:headline`, `schema:alternativeHeadline`, and the
  page title, and no `HarvestedArc` MUST be returned

### Requirement: OpenAgrar title fallbacks MUST be traceable

A title resolved from any carrier other than `schema:name` SHALL NOT be silent. The mapped Investigation SHALL carry a
Comment named `Title Source` whose text identifies the winning carrier (`headline`, `alternativeHeadline`, or
`html_title`), and the mapper SHALL emit a WARNING log line naming the Dataset subject, the carrier, and the resolved
title. A title taken from `schema:name` SHALL NOT produce either signal.

#### Scenario: Headline fallback is recorded and logged

- **WHEN** the title is resolved from `schema:headline`
- **THEN** the Investigation MUST contain `Comment("Title Source", "headline")` and a WARNING log record mentioning
  `headline` MUST be emitted

#### Scenario: schema:name produces no provenance comment

- **WHEN** the title is resolved from a non-empty `schema:name`
- **THEN** the Investigation MUST NOT contain a `Title Source` comment and no title-fallback WARNING MUST be emitted
