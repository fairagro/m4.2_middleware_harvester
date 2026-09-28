## Purpose

Bounds harvested INSPIRE CSW/ISO-19139 values so a hostile or broken endpoint cannot inject unbounded strings, unbounded
lists, or non-http(s) URLs into an ARC, and adds matching config-level bounds on `csw_url` and `max_records`. Defensive
only — does not validate the semantic correctness of a value (see
`openspec/changes/archive/ 2026-09-22-harden-csw-xml-parsing/proposal.md` for the related XML-hardening requirement, and
issue #132 for semantic/data-quality validation, out of scope here).

## ADDED Requirements

### Requirement: Harvested free-text fields are length-bounded

The system SHALL truncate every string value extracted from a CSW/ISO-19139 record by `IsoParser` to a fixed maximum
length before it reaches `InspireRecord`. The system SHALL NOT reject or fail a record solely because a free-text field
exceeded its bound.

#### Scenario: Oversized title is truncated, not rejected

- **WHEN** a harvested record's title exceeds the configured maximum length
- **THEN** `InspireRecord.title` holds the truncated value, and parsing succeeds

#### Scenario: Oversized abstract is truncated, not rejected

- **WHEN** a harvested record's abstract exceeds the configured maximum length
- **THEN** `InspireRecord.abstract` holds the truncated value, and parsing succeeds

### Requirement: Harvested list fields are count-bounded

The system SHALL cap every list field on `InspireRecord` populated from harvested CSW/ISO-19139 data to a fixed maximum
number of elements. Elements beyond the cap SHALL be dropped, not cause the record to fail.

#### Scenario: Oversized keyword list is capped

- **WHEN** a harvested record's keyword list exceeds the configured maximum item count
- **THEN** `InspireRecord.keywords` holds at most that maximum number of elements, and parsing succeeds

### Requirement: Harvested URL values are restricted to http(s)

The system SHALL accept a harvested URL value only if it parses as an absolute URL with scheme `http` or `https`. A
value with any other scheme (including no scheme, e.g. a protocol-relative URL) SHALL be dropped: the corresponding
optional field is set to `None`, or the element is omitted from its list, rather than failing the record.

#### Scenario: Dangerous-scheme URL is dropped from an optional field

- **WHEN** a harvested `graphicoverview`/`otherconstraints_url`/`lineage_url`/etc. value has a `javascript:`, `file:`,
  `data:`, `ftp:`, or protocol-relative form
- **THEN** that value is omitted from the corresponding field, and parsing succeeds

#### Scenario: A required OnlineResource with an invalid URL is dropped entirely

- **GIVEN** an online-resource entry whose `url` fails the http(s) check
- **WHEN** the record is parsed
- **THEN** that online-resource entry is omitted from `InspireRecord.online_resources` entirely — no `OnlineResource` is
  constructed with an invalid required `url`

#### Scenario: A well-formed http(s) URL passes through unchanged

- **WHEN** a harvested URL value has scheme `http` or `https` and a non-empty host
- **THEN** the value is preserved unchanged in the corresponding field

### Requirement: A malformed spatial-resolution denominator does not fail the record

The system SHALL skip a scale-denominator value that cannot be parsed as an integer, rather than propagating the
coercion error and failing the whole record.

#### Scenario: One bad denominator among good ones is dropped, others kept

- **GIVEN** a record whose denominators list contains both numeric and non-numeric values
- **WHEN** the record is parsed
- **THEN** `InspireRecord.spatial_resolution_denominators` contains only the numeric values, in order, and parsing does
  not raise

### Requirement: INSPIRE identifier sanitization reuses the shared payload helper

`middleware.inspire.mapper.InspireMapper` SHALL use `middleware.payload.identifier_sanitizer.to_identifier_slug` for
title-derived identifier slugs, and SHALL apply `middleware.payload.identifier_sanitizer.sanitize_identifier` to every
ARC investigation identifier derived from a harvested record, whether or not that identifier is URL-shaped.

#### Scenario: A raw non-URL-shaped identifier is character-sanitized

- **GIVEN** a harvested record whose identifier is not URL-shaped (contains neither `://` nor `/`) and contains
  characters outside the identifier allowlist
- **WHEN** the record is mapped to an `ArcInvestigation`
- **THEN** the resulting identifier contains only allowlisted characters

### Requirement: Config validates csw_url as an http(s) URL

`middleware.inspire.config.Config` SHALL reject a `csw_url` value that does not parse as an absolute `http` or `https`
URL, raising a validation error at construction time.

#### Scenario: Non-http(s) csw_url is rejected

- **WHEN** `Config` is constructed with a `csw_url` using a scheme other than `http` or `https` (or no scheme)
- **THEN** construction raises a validation error

#### Scenario: http(s) csw_url is accepted

- **WHEN** `Config` is constructed with an `http://` or `https://` `csw_url`
- **THEN** construction succeeds and `csw_url` is unchanged

### Requirement: Config bounds an explicitly-set max_records, leaving the unbounded default untouched

`middleware.inspire.config.Config.max_records` SHALL accept values from 1 up to 1,000,000 inclusive when explicitly set,
and SHALL continue to accept `None` (meaning "harvest all records") as its unconstrained default.

#### Scenario: Value over the ceiling is rejected

- **WHEN** `Config` is constructed with `max_records` greater than 1,000,000
- **THEN** construction raises a validation error

#### Scenario: Omitted max_records remains unbounded

- **WHEN** `Config` is constructed without setting `max_records`
- **THEN** `max_records` is `None`, and construction succeeds
