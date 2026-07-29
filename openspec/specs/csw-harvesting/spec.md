# CSW Harvesting

## Purpose

Query the Catalogue Service for Web (CSW) endpoints and parse ISO 19139 XML into the `InspireRecord` object.

## Requirements

### Requirement: Connect securely to the configured csw_url and retrieve all available…
The system SHALL ensure that connect securely to the configured `csw_url` and retrieve all available metadata records.

#### Scenario: Satisfies — Connect securely to the configured csw_url and retrieve all available…
- **WHEN** the conditions described by this requirement apply
- **THEN** Connect securely to the configured `csw_url` and retrieve all available metadata records

### Requirement: Support four mutually exclusive query modes per call:
The system SHALL ensure that support four mutually exclusive query modes per call:.

#### Scenario: Satisfies — Support four mutually exclusive query modes per call:
- **WHEN** the conditions described by this requirement apply
- **THEN** Support four mutually exclusive query modes per call:

### Requirement: For xml_query pagination, use config chunk_size as the page size…
The system SHALL ensure that for `xml_query` pagination, use config `chunk_size` as the page size unless the XML root specifies a valid `maxRecords` (> 0), which overrides `chunk_size` for the page size only.

#### Scenario: Satisfies — For xml_query pagination, use config chunk_size as the page size…
- **WHEN** the conditions described by this requirement apply
- **THEN** For `xml_query` pagination, use config `chunk_size` as the page size unless the XML root specifies a valid `maxRecords` (> 0), which overrides `chunk_size` for the page size only

### Requirement: For xml_query pagination, start at position 1 unless the XML…
The system SHALL ensure that for `xml_query` pagination, start at position 1 unless the XML root specifies a valid `startPosition` (≥ 1), which is the initial page offset.

#### Scenario: Satisfies — For xml_query pagination, start at position 1 unless the XML…
- **WHEN** the conditions described by this requirement apply
- **THEN** For `xml_query` pagination, start at position 1 unless the XML root specifies a valid `startPosition` (≥ 1), which is the initial page offset

### Requirement: Cap the total number of harvested records with config max_records…
The system SHALL ensure that cap the total number of harvested records with config `max_records` when set (all query modes); do not treat XML `maxRecords` as a harvest-wide limit.

#### Scenario: Satisfies — Cap the total number of harvested records with config max_records…
- **WHEN** the conditions described by this requirement apply
- **THEN** Cap the total number of harvested records with config `max_records` when set (all query modes); do not treat XML `maxRecords` as a harvest-wide limit

### Requirement: Enforce mutual exclusion: activating more than one query mode (combining…
The system SHALL ensure that enforce mutual exclusion: activating more than one query mode (combining call-site arguments with Config defaults) must raise `ValueError` immediately, before any network call.

#### Scenario: Satisfies — Enforce mutual exclusion: activating more than one query mode (combining…
- **WHEN** the conditions described by this requirement apply
- **THEN** Enforce mutual exclusion: activating more than one query mode (combining call-site arguments with Config defaults) must raise `ValueError` immediately, before any network call

### Requirement: Parse each ISO 19139 batch and yield RecordProcessingError for every…
The system SHALL parse each ISO 19139 batch and yield `RecordProcessingError` for every record whose XML cannot be parsed, using the ISO identifier where available.

#### Scenario: Satisfies — Parse each ISO 19139 batch and yield RecordProcessingError for every…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse each ISO 19139 batch and yield `RecordProcessingError` for every record whose XML cannot be parsed, using the ISO identifier where available

### Requirement: If and only if a batch contains ISO records without…
The system SHALL ensure that if and only if a batch contains ISO records without a usable identifier (absent or `owslib_random_*`), fetch the corresponding Dublin Core batch to obtain stable identifiers for those records.

#### Scenario: Satisfies — If and only if a batch contains ISO records without…
- **WHEN** the conditions described by this requirement apply
- **THEN** If and only if a batch contains ISO records without a usable identifier (absent or `owslib_random_*`), fetch the corresponding Dublin Core batch to obtain stable identifiers for those records

### Requirement: Match DC identifiers to identifier-less ISO parse errors by associating…
The system SHALL ensure that match DC identifiers to identifier-less ISO parse errors by associating the remaining (unmatched) DC identifiers with failed ISO records in positional order.

#### Scenario: Satisfies — Match DC identifiers to identifier-less ISO parse errors by associating…
- **WHEN** the conditions described by this requirement apply
- **THEN** Match DC identifiers to identifier-less ISO parse errors by associating the remaining (unmatched) DC identifiers with failed ISO records in positional order

### Requirement: Yield a RecordProcessingError for each unmatched DC identifier so that…
The system SHALL ensure that yield a `RecordProcessingError` for each unmatched DC identifier so that the harvest report can attribute errors to a specific source record.

#### Scenario: Satisfies — Yield a RecordProcessingError for each unmatched DC identifier so that…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield a `RecordProcessingError` for each unmatched DC identifier so that the harvest report can attribute errors to a specific source record

### Requirement: Edge case — - ISO records with a valid identifier parse fine
The system SHALL handle this edge case: when - ISO records with a valid identifier parse fine, then DC is never fetched for that batch. - A batch is completely identifier-less (all records empty/broken) → DC batch fetched; all DC identifiers treated as failed records. - DC batch itself fails (network error) → log warning; ISO parse errors are reported without identifiers (message includes position in batch). - Broken XML responses or invalid attribute access → yield `RecordProcessingError`, continue iteration. - `fes_constraints` has no Config-level equivalent because OWSLib `OgcExpression` objects are runtime-only and not YAML-serializable; it can only be supplied at call time. - An XML query with an encoding declaration must be converted to `bytes` before being passed to OWSLib to avoid an lxml `Unicode strings with encoding declaration` error. - `xml_query` whose root is not CSW 2.0.2 `GetRecords` in the CSW namespace (wrong element, nested, unnamespaced, or non-CSW namespace) → raise `ValueError` before any network call. - `xml_query` with invalid / non-positive `maxRecords` or `startPosition` → ignore that attribute, log a warning, and fall back to config / default (same as if omitted). - `xml_query` plus config `max_records=N` → stop after N successfully counted records across pages (same semantics as CQL/standard); the final page is truncated so the success yield count does not exceed N, while `RecordProcessingError` items from that page are still yielded. - Operator sets XML `maxRecords="10"` and config `chunk_size=50` → each page requests 10 records; harvest continues across pages until exhausted or `max_records` stops it. - `xml_query` with a non-ISO `outputSchema` → override to ISO 19139 (`gmd`) on each ISO request copy (warned once at prepare); the shared template is not mutated; Dublin Core fallback still switches schema on its own copy.

#### Scenario: Edge case — - ISO records with a valid identifier parse fine
- **WHEN** - ISO records with a valid identifier parse fine
- **THEN** DC is never fetched for that batch. - A batch is completely identifier-less (all records empty/broken) → DC batch fetched; all DC identifiers treated as failed records. - DC batch itself fails (network error) → log warning; ISO parse errors are reported without identifiers (message includes position in batch). - Broken XML responses or invalid attribute access → yield `RecordProcessingError`, continue iteration. - `fes_constraints` has no Config-level equivalent because OWSLib `OgcExpression` objects are runtime-only and not YAML-serializable; it can only be supplied at call time. - An XML query with an encoding declaration must be converted to `bytes` before being passed to OWSLib to avoid an lxml `Unicode strings with encoding declaration` error. - `xml_query` whose root is not CSW 2.0.2 `GetRecords` in the CSW namespace (wrong element, nested, unnamespaced, or non-CSW namespace) → raise `ValueError` before any network call. - `xml_query` with invalid / non-positive `maxRecords` or `startPosition` → ignore that attribute, log a warning, and fall back to config / default (same as if omitted). - `xml_query` plus config `max_records=N` → stop after N successfully counted records across pages (same semantics as CQL/standard); the final page is truncated so the success yield count does not exceed N, while `RecordProcessingError` items from that page are still yielded. - Operator sets XML `maxRecords="10"` and config `chunk_size=50` → each page requests 10 records; harvest continues across pages until exhausted or `max_records` stops it. - `xml_query` with a non-ISO `outputSchema` → override to ISO 19139 (`gmd`) on each ISO request copy (warned once at prepare); the shared template is not mutated; Dublin Core fallback still switches schema on its own copy
