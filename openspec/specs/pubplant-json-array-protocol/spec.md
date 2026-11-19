# PubPlant JSON Array Protocol

## Purpose

Generic-plugin `Protocol` that discovers records from a single, non-paginated JSON array of inline JSON-LD records (e.g.
PlabiPD/PubPlant `genomes.json`).

## Requirements

### Requirement: Register a pubplant_json_array Protocol

The system SHALL register a `Protocol` implementation under `ProtocolType.pubplant_json_array` whose canonical entry
point is nested `generic.protocol.pubplant_json_array.entry_url`.

#### Scenario: pubplant_json_array resolves from the registry

- **WHEN** a generic repository sets nested `protocol.pubplant_json_array.entry_url`
- **THEN** config validation and `GenericPlugin.create_protocol` resolve the PubPlant JSON array Protocol

### Requirement: Fetch the whole array in one request

The Protocol SHALL fetch `entry_url` once per discovery and MUST fail with `GenericProtocolError` when the response is
not valid JSON or its top level is not a JSON array. HTTP and transport errors propagate unchanged; `GenericPlugin`
wraps them like any other Protocol failure.

#### Scenario: Non-array response

- **WHEN** the response body is a JSON object
- **THEN** discovery fails with a `GenericProtocolError` naming the expected JSON array

### Requirement: Yield one inline JSON-LD unit per object element

For each object element the Protocol SHALL yield a `JsonLdDiscoveryResult` whose `payload` is the element (after the
identifier whitespace repair and the doubled-resolver repair) and whose `identifier` and `harvest_source_id` are
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

- **GIVEN** an element with whitespace or a doubled resolver in its DOI and the same element already fixed
- **WHEN** each is discovered
- **THEN** both get the same identifier and payload

#### Scenario: Records without whitespace are unchanged

- **GIVEN** an element with no whitespace and no doubled resolver in `@id` or `identifier`
- **WHEN** it is discovered
- **THEN** its identifier and payload are the same as before this change

### Requirement: Expected count is unknown

The Protocol SHALL report no expected count and SHALL NOT fetch the array to compute one, because
`GenericPlugin.get_expected_datasets()` and `run()` use separate Protocol instances and counting would download the
whole array a second time.

#### Scenario: No extra fetch for the count

- **WHEN** `get_expected_count()` is called
- **THEN** it returns `None` without issuing an HTTP request

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

### Requirement: Collapse doubled DOI resolvers in record identifiers

Before computing identity and yielding a record, the Protocol SHALL remove every stacked DOI resolver prefix
(`doi.org/`, `dx.doi.org/` or `www.doi.org/`, each with or without `http://` or `https://`) from the start of the
record's top-level `@id` and `identifier` string values when what remains is a DOI (`10.<digits>/…`), writing `@id` as
`https://doi.org/<doi>` and `identifier` as the bare `<doi>`, and SHALL log one WARNING per repaired record naming each
repaired field with its original value. A value whose remainder is not a DOI, and all other fields, MUST be left
unchanged.

#### Scenario: Doubled resolver yields the DOI

- **GIVEN** an element with `@id` `https://doi.org/doi.org/10.1093/dnares/dsx047` and `identifier`
  `doi.org/10.1093/dnares/dsx047`
- **WHEN** PlabiPD is harvested
- **THEN** the ARC carries the DOI `10.1093/dnares/dsx047`

#### Scenario: No doubled resolver in the ARC

- **GIVEN** that element
- **WHEN** it is mapped
- **THEN** no ARC value contains `doi.org/doi.org` and the link is `https://doi.org/10.1093/dnares/dsx047`

#### Scenario: Repair is logged

- **GIVEN** an element whose `@id` or `identifier` has a doubled resolver
- **WHEN** it is discovered
- **THEN** one WARNING names each repaired field with its original value

#### Scenario: Free-text identifier is untouched

- **GIVEN** an element whose `identifier` is `Genome Assembly 12`
- **WHEN** it is discovered
- **THEN** the payload is unchanged and no WARNING is logged
