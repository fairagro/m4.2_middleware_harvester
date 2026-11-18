# Spec Delta

## ADDED Requirements

### Requirement: Repair whitespace in record identifiers

Before computing identity and yielding a record, the Protocol SHALL remove every whitespace character from the record's
top-level `@id` string value and from its top-level `identifier` string value when that value is DOI-like
(`10.<digits>/…`), and SHALL log one WARNING per repaired record naming each repaired field with its original value.
Other fields, and any `identifier` that is not DOI-like, MUST be left unchanged.

#### Scenario: DOI with a space is harvested

- **GIVEN** an element whose `@id` and `identifier` are `https://doi.org/10.1038/ s41597-026-06582-z`
- **WHEN** PlabiPD is harvested
- **THEN** the record is harvested, not reported as failed

#### Scenario: Mapped DOI has no whitespace

- **GIVEN** that element
- **WHEN** it is mapped
- **THEN** the ARC carries the identifier `https://doi.org/10.1038/s41597-026-06582-z`

#### Scenario: Repair is logged

- **GIVEN** an element whose `@id` or DOI-like `identifier` contains whitespace
- **WHEN** it is discovered
- **THEN** one WARNING names each repaired field with its original value, and not the fields that were clean

#### Scenario: Free-text identifier is untouched

- **GIVEN** an element whose `identifier` is `Genome Assembly 12`
- **WHEN** it is discovered
- **THEN** the payload is unchanged and no WARNING is logged

## MODIFIED Requirements

### Requirement: Yield one inline JSON-LD unit per object element

For each object element the Protocol SHALL yield a `JsonLdDiscoveryResult` whose `payload` is the element (after the
identifier whitespace repair) and whose `identifier` and `harvest_source_id` are
`sanitize_identifier(@id or identifier) + ":" + <16 hex chars of the SHA-256 of the element's canonical JSON>` (only the
hash when no id is present), both computed from the repaired element. A non-object element SHALL yield a
`RecordProcessingError` with record id `pubplant_json_array:index=<n>` without stopping discovery.

#### Scenario: Records sharing a DOI stay distinct

- **WHEN** two elements share `@id` but differ in content
- **THEN** both are discovered with distinct identifiers that share the sanitized DOI prefix

#### Scenario: Identical records collapse

- **WHEN** two elements are byte-identical in canonical JSON
- **THEN** the second is reported as a `SkippedRecord` duplicate

#### Scenario: Re-ordered array

- **WHEN** the same records are served in a different order
- **THEN** the set of discovered identifiers is unchanged

#### Scenario: Provider fix keeps the identifier

- **GIVEN** an element with whitespace in its DOI and the same element with the whitespace already removed
- **WHEN** each is discovered
- **THEN** both get the same identifier

#### Scenario: Records without whitespace are unchanged

- **GIVEN** an element with no whitespace in `@id` or `identifier`
- **WHEN** it is discovered
- **THEN** its identifier and payload are the same as before this change
