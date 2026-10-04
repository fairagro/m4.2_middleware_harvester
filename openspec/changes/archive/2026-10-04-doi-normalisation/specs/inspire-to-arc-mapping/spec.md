## ADDED Requirements

### Requirement: DOIs MUST be bare and normalised

`InspireMapper` MUST pass each citation resource identifier code (else its URL) through
`middleware.payload.dois.normalize_doi`, which strips any number of `doi:`, `https://doi.org/`, `https://dx.doi.org/`
and `https://www.doi.org/` prefixes and returns the bare `10.<registrant>/<suffix>` DOI. Each distinct DOI
(case-insensitive) MUST become one Publication with that bare DOI. Codes that are not DOIs MUST NOT become Publications.
The Schema.org and Regal mappers MUST use the same helper.

#### Scenario: GeoNode stacked prefixes

- **WHEN** a resource identifier code is `doi:https://doi.org/10.4228/zalf.vjcp-vep3` with URL
  `https://dx.doi.org/https://doi.org/10.4228/zalf.vjcp-vep3`
- **THEN** the RO-Crate citation `identifier` MUST be `10.4228/zalf.vjcp-vep3`

#### Scenario: Not a DOI

- **WHEN** a resource identifier code is an ISBN or `doi:https://www.ncbi.nlm.nih.gov/…`
- **THEN** no Publication MUST be created for it
