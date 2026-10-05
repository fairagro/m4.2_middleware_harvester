## ADDED Requirements

### Requirement: Person affiliation MUST fall back to a flat address

`GeneralSchemaOrgMapper` MUST set `Person.Affiliation` from `schema:affiliation` (Organization `name` or string). When
there is no affiliation and `schema:address` is a plain string, the affiliation MUST be its first non-empty
comma-separated segment, and `Person.Address` MUST keep the full string. A plain-string address made only of commas and
whitespace MUST be absent. A `PostalAddress` MUST be flattened as
`streetAddress, postalCode, addressLocality, addressRegion, addressCountry` (missing parts skipped) and MUST NOT give an
affiliation.

#### Scenario: e!DAL flat address

- **WHEN** a Person has no affiliation and the address "Leibniz Institute of Plant Genetics and Crop Plant Research
  (IPK), Seeland OT Gatersleben, Corrensstraße 3, D-06466, Germany"
- **THEN** the affiliation MUST be "Leibniz Institute of Plant Genetics and Crop Plant Research (IPK)" and the address
  MUST be the full string

#### Scenario: Explicit affiliation

- **WHEN** a Person has an affiliation Organization named "Thünen Institute" and a flat address
- **THEN** the affiliation MUST be "Thünen Institute"

#### Scenario: Empty flat address

- **WHEN** a Person's address is `" ,  , "`
- **THEN** the Person MUST have neither an address nor an affiliation
