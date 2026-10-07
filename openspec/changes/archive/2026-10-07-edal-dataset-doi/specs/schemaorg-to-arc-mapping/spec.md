## ADDED Requirements

### Requirement: A bare-DOI @id MUST give the dataset DOI

The `html_jsonld` and `jsonld` parsers MUST turn every JSON-LD `@id` that is a bare DOI (`10.<registrant>/<suffix>`)
into `https://doi.org/<doi>` before parsing, so it is never resolved against the working directory.
`GeneralSchemaOrgMapper` MUST then use that DOI as the dataset DOI (Publication DOI) when `schema:identifier` has none.
The Investigation identifier MUST NOT change.

#### Scenario: e!DAL landing page

- **WHEN** the page `https://doi.org/10.5447/ipk/2011/0` has a Dataset with `"@id": "10.5447/ipk/2011/0"` and no
  `schema:identifier`
- **THEN** the RO-Crate MUST have a `PropertyValue` named `DOI` with value `10.5447/ipk/2011/0`, and the Investigation
  identifier MUST stay `doi_org_10_5447_ipk_2011_0`
