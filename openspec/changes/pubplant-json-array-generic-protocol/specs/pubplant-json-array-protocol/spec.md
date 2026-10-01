# PubPlant JSON Array Protocol

## Purpose

Generic-plugin `Protocol` that discovers records from a single, non-paginated JSON array of inline JSON-LD records (e.g.
PlabiPD/PubPlant `genomes.json`).

## ADDED Requirements

### Requirement: Register a pubplant_json_array Protocol

The system SHALL register a `Protocol` implementation under `ProtocolType.pubplant_json_array`
(`generic.protocol_type: pubplant_json_array`) whose entry point is `generic.sitemap_url`.

#### Scenario: pubplant_json_array resolves from the registry

- **WHEN** a generic repository sets `protocol_type: pubplant_json_array`
- **THEN** config validation and `GenericPlugin.create_protocol` resolve the PubPlant JSON array Protocol

### Requirement: Fetch the whole array in one request

The Protocol SHALL fetch `sitemap_url` once per discovery and MUST fail with `GenericProtocolError` when the response is
not valid JSON or its top level is not a JSON array. HTTP and transport errors propagate unchanged; `GenericPlugin`
wraps them like any other Protocol failure.

#### Scenario: Non-array response

- **WHEN** the response body is a JSON object
- **THEN** discovery fails with a `GenericProtocolError` naming the expected JSON array

### Requirement: Yield one inline JSON-LD unit per object element

For each object element the Protocol SHALL yield a `JsonLdDiscoveryResult` whose `payload` is the element and whose
`identifier` and `harvest_source_id` are
`sanitize_identifier(@id or identifier) + ":" + <16 hex chars of the SHA-256 of the element's canonical JSON>` (only the
hash when no id is present). A non-object element SHALL yield a `RecordProcessingError` with record id
`pubplant_json_array:index=<n>` without stopping discovery.

#### Scenario: Records sharing a DOI stay distinct

- **WHEN** two elements share `@id` but differ in content
- **THEN** both are discovered with distinct identifiers that share the sanitized DOI prefix

#### Scenario: Identical records collapse

- **WHEN** two elements are byte-identical in canonical JSON
- **THEN** the second is reported as a `SkippedRecord` duplicate

#### Scenario: Re-ordered array

- **WHEN** the same records are served in a different order
- **THEN** the set of discovered identifiers is unchanged

### Requirement: Expected count is unknown

The Protocol SHALL report no expected count and SHALL NOT fetch the array to compute one, because
`GenericPlugin.get_expected_datasets()` and `run()` use separate Protocol instances and counting would download the
whole array a second time.

#### Scenario: No extra fetch for the count

- **WHEN** `get_expected_count()` is called
- **THEN** it returns `None` without issuing an HTTP request
