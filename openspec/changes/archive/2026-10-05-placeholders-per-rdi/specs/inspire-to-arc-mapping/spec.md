## MODIFIED Requirements

### Requirement: Placeholder values in optional INSPIRE fields MUST be treated as absent

`InspireRecord` and its nested models MUST treat a value of an optional field as absent when the whole value matches the
repository's `mapper.placeholders` (case-insensitive, surrounding whitespace ignored): a scalar MUST fall back to the
field default and list items MUST be removed. `InspirePlugin` MUST pass the `PlaceholderConfig` through `CSWClient` and
`IsoParser` into the validation context (`PLACEHOLDERS_CONTEXT_KEY`); `CSWClient` and `IsoParser` MUST require it. Only
without a validation context (direct model construction) the `PlaceholderConfig` model defaults MUST apply, which match
nothing. Required fields (`identifier`, `title`, `abstract`) MUST keep their value.

#### Scenario: GeoNode "None" in optional elements

- **WHEN** the repository's `mapper.placeholders.values` is ["None", "No information provided"]
- **AND** a record has `purpose` "None", `supplementalInformation` "No information provided" and `graphicOverview`
  ["None", "https://example.com/thumb.png"]
- **THEN** `purpose` and `supplemental_information` MUST be `None` and `graphic_overviews` MUST be
  ["https://example.com/thumb.png"], and the record MUST validate

#### Scenario: Placeholder abstract

- **WHEN** the repository's `mapper.placeholders.values` is ["No abstract provided"]
- **AND** a record has the abstract "No abstract provided"
- **THEN** `abstract` MUST stay "No abstract provided"

#### Scenario: Only configured values

- **WHEN** the repository's `mapper.placeholders.values` is ["Keine Angabe"]
- **THEN** `purpose` "keine angabe" MUST be absent and `edition` "None" MUST be kept

#### Scenario: Nothing configured

- **WHEN** the repository has no `mapper.placeholders`
- **THEN** `purpose` "None" MUST be kept
