## ADDED Requirements

### Requirement: Free-text constraint elements use the paragraph limit

Each element of `InspireRecord.other_constraints` (`gmd:otherConstraints`) and `InspireRecord.constraints`
(`gmd:useLimitation`) SHALL be bounded by `max_str_long`, because ISO 19139 defines them as free text. Each element of
the codelist-valued constraint lists (`access_constraints`, `use_constraints`, `classification`) SHALL remain bounded by
`max_str_medium`.

#### Scenario: Long disclaimer in otherConstraints is accepted

- **WHEN** a harvested record's `gmd:otherConstraints` element is longer than `max_str_medium` but within `max_str_long`
- **THEN** the record parses and `other_constraints` holds the full, untruncated text

#### Scenario: Long useLimitation is accepted

- **WHEN** a harvested record's `gmd:useLimitation` element is longer than `max_str_medium` but within `max_str_long`
- **THEN** the record parses and `constraints` holds the full, untruncated text

#### Scenario: Free-text constraint over the paragraph limit is rejected

- **WHEN** a harvested `gmd:otherConstraints` or `gmd:useLimitation` element exceeds `max_str_long`
- **THEN** parsing raises a validation error and no `InspireRecord` is produced

#### Scenario: Codelist constraint keeps the single-line limit

- **WHEN** a harvested `gmd:accessConstraints` value exceeds `max_str_medium`
- **THEN** parsing raises a validation error
