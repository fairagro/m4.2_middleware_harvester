## ADDED Requirements

### Requirement: Regal language MUST be an ISO 639 code

`RegalMapper` MUST write the `Language` Investigation comment and Assay `Comment [Language]` column from
`dcterms:language` as the ISO 639 code taken from an `id.loc.gov/vocabulary/iso639-1/<code>` or
`id.loc.gov/vocabulary/iso639-2/<code>` IRI, in lower case. It MUST use the `prefLabel` only when the value has no such
IRI. Duplicate values MUST be written once, joined with `; `.

#### Scenario: Localised label with a LoC IRI

- **WHEN** a record has `language: [{"prefLabel": "Englisch", "@id": "http://id.loc.gov/vocabulary/iso639-2/eng"}]`
- **THEN** the `Language` comment MUST be `eng` and the ARC MUST NOT contain `Englisch`

#### Scenario: No LoC IRI

- **WHEN** a language value is a blank node with `prefLabel` "Plattdeutsch"
- **THEN** the `Language` comment MUST contain `Plattdeutsch`
