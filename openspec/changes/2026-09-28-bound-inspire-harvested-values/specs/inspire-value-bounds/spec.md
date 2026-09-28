## Purpose

Validates harvested INSPIRE CSW/ISO-19139 values on the `InspireRecord` model so a hostile or broken endpoint cannot
inject unbounded strings, unbounded lists, disallowed URL schemes or non-conformant codelist values into an ARC. Limits
are configurable; a violating record is reported as failed, never silently altered. Plausibility of conformant values
(bounding-box ranges, URL reachability) is out of scope (issue #132).

## ADDED Requirements

### Requirement: Validation limits are configurable

`middleware.inspire.config.Config` SHALL provide a `value_bounds` section with defaulted fields `max_str_short` (200),
`max_str_medium` (1,000), `max_str_long` (10,000), `max_list_items` (500) and `allowed_url_schemes` (`http`, `https`,
`ftp`). Integer limits SHALL be at least 1 and `allowed_url_schemes` SHALL be non-empty.

#### Scenario: Defaults apply when value_bounds is omitted

- **WHEN** `Config` is constructed without `value_bounds`
- **THEN** `value_bounds` holds the default limits

#### Scenario: Configured limits are enforced

- **GIVEN** `value_bounds.max_list_items` is 2
- **WHEN** a harvested record with 3 keywords is parsed
- **THEN** parsing raises a validation error naming `max_list_items`

### Requirement: Harvested values violating a limit fail the record, unaltered

The system SHALL validate every string and list field of `InspireRecord` and its nested models against the configured
limits. A record with a violating value SHALL fail validation; the system SHALL NOT truncate strings or drop list
elements to make it pass. The failure SHALL be reported as a failed record (`RecordProcessingError`).

#### Scenario: Oversized identifier is rejected, not truncated

- **WHEN** a harvested record's `fileIdentifier` exceeds `max_str_medium`
- **THEN** parsing raises a validation error and no `InspireRecord` is produced

#### Scenario: Oversized list is rejected

- **WHEN** a harvested record's keyword list exceeds `max_list_items`
- **THEN** parsing raises a validation error

#### Scenario: Error does not echo the oversized value

- **WHEN** a harvested value of 50,000 characters is rejected
- **THEN** the error message is shorter than 1,000 characters

### Requirement: Harvested URLs are restricted to allowed schemes

The system SHALL accept a harvested URL value only if it has a scheme in `value_bounds.allowed_url_schemes`, a non-empty
host, and a length within `max_str_medium`. A blank value in an optional URL field SHALL be treated as absent.
`dataset_uri` SHALL additionally accept a URN.

#### Scenario: Dangerous-scheme URL fails the record

- **WHEN** a harvested graphic-overview or online-resource URL uses `javascript:`, `file:`, `data:` or is
  protocol-relative
- **THEN** parsing raises a validation error

#### Scenario: ftp download link is accepted by default

- **WHEN** a harvested online-resource URL uses `ftp://`
- **THEN** parsing succeeds and the URL is unchanged

#### Scenario: Blank optional URL is absent

- **WHEN** a harvested optional URL field is an empty or whitespace string
- **THEN** parsing succeeds and the field is `None`

#### Scenario: URN dataset URI is accepted

- **WHEN** a harvested `dataSetURI` is a URN
- **THEN** parsing succeeds and `dataset_uri` holds the URN

### Requirement: Coded fields conform to ISO 19139 codelists and formats

The system SHALL validate `charset` (MD_CharacterSetCode), `hierarchy` (MD_ScopeCode), `status` (MD_ProgressCode),
`Contact.role` (CI_RoleCode), `InspireDate.datetype` and `ConformanceResult.specification_datetype` (CI_DateTypeCode)
and `topic_categories` (MD_TopicCategoryCode), each including ISO 19115-1 additions; `language` and `resource_language`
as ISO 639-2 three-letter codes; `date_stamp` and date fields as ISO 8601; `Contact.email` as a single-`@`,
whitespace-free address; and `ConformanceResult.degree` as `gco:Boolean`. A non-conformant value SHALL fail the record.
Spatial-resolution denominators SHALL be integers.

#### Scenario: ISO 639-1 language code is rejected

- **WHEN** a harvested record's language is `de`
- **THEN** parsing raises a validation error

#### Scenario: Non-codelist character set is rejected

- **WHEN** a harvested record's character set is `utf-8`
- **THEN** parsing raises a validation error

#### Scenario: Malformed denominator is rejected

- **WHEN** a harvested record's denominators include a non-numeric value
- **THEN** parsing raises a validation error

### Requirement: ARC identifiers are derived without placeholders

`middleware.inspire.mapper.InspireMapper` SHALL use `middleware.payload.identifier_sanitizer` for identifier slugs and
SHALL allowlist-sanitize every investigation identifier. It SHALL NOT use a placeholder identifier. Study and assay
identifiers SHALL fall back from the title slug to the sanitized `fileIdentifier`. When no non-empty identifier can be
derived, mapping SHALL fail with `SemanticError`.

#### Scenario: Raw identifier is character-sanitized

- **WHEN** a record whose `fileIdentifier` is `weird id!@#` is mapped
- **THEN** the investigation identifier contains only allowlisted characters

#### Scenario: Title without slug falls back to the fileIdentifier

- **GIVEN** a record whose title yields no slug and whose `fileIdentifier` is `rec-42`
- **WHEN** the record is mapped
- **THEN** the study and assay identifiers are `rec-42`

#### Scenario: No derivable identifier fails mapping

- **WHEN** a record whose `fileIdentifier` sanitizes to an empty string is mapped
- **THEN** mapping raises `SemanticError`

### Requirement: Config validates csw_url as an http(s) URL

`Config` SHALL reject a `csw_url` that is not an absolute `http` or `https` URL, raising a validation error at
construction time. This is a functional constraint of the OWSLib transport and SHALL NOT be configurable. `max_records`
SHALL impose no upper ceiling.

#### Scenario: Non-http(s) csw_url is rejected

- **WHEN** `Config` is constructed with an `ftp://` `csw_url`
- **THEN** construction raises a validation error

#### Scenario: Large max_records is accepted

- **WHEN** `Config` is constructed with `max_records` of 5,000,000
- **THEN** construction succeeds
