# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
