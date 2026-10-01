## ADDED Requirements

### Requirement: Register phenoroam_xml parser type

The system SHALL register a PayloadParser implementation under registry key `phenoroam_xml` selectable via repository
`parser.type`, with `produces` kind `phenoroam_record`.

#### Scenario: phenoroam_xml produces phenoroam_record

- **WHEN** `parser.type` is `phenoroam_xml`
- **THEN** the parser’s `produces` kind is `phenoroam_record`

#### Scenario: oai_pmh can compose phenoroam_xml with phenoroam_general mapper

- **WHEN** an `oai_pmh` repository sets `parser: { type: phenoroam_xml }` and `mapper: { type: phenoroam_general }`
- **THEN** startup kind alignment succeeds
