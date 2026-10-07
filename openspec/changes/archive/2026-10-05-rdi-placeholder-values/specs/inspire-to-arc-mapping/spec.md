## ADDED Requirements

### Requirement: Placeholder values in optional INSPIRE fields MUST be treated as absent

`InspireRecord` and its nested models MUST treat a value of an optional field as absent when the whole value matches
`value_bounds.placeholder_values` (case-insensitive, surrounding whitespace ignored) or is an unrendered `$var`,
`${var}` or `{{var}}` template: a scalar MUST fall back to the field default and list items MUST be removed. The default
list MUST be `None`, `null`, `N/A`, `No abstract provided`, `Keine Zusammenfassung vorhanden` and
`No information provided`. Required fields (`identifier`, `title`, `abstract`) MUST keep their value.

#### Scenario: GeoNode "None" in optional elements

- **WHEN** a record has `purpose` "None", `supplementalInformation` "No information provided" and `graphicOverview`
  ["None", "https://example.com/thumb.png"]
- **THEN** `purpose` and `supplemental_information` MUST be `None` and `graphic_overviews` MUST be
  ["https://example.com/thumb.png"], and the record MUST validate

#### Scenario: Placeholder abstract

- **WHEN** a record has the abstract "No abstract provided"
- **THEN** `abstract` MUST stay "No abstract provided"

#### Scenario: Configured list

- **WHEN** `value_bounds.placeholder_values` is ["Keine Angabe"]
- **THEN** `purpose` "keine angabe" MUST be absent and `edition` "None" MUST be kept
