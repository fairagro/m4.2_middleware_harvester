## ADDED Requirements

### Requirement: dcterms:issued MUST be datePublished

`CkanextDcatMapper` MUST set Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`) from
`dcterms:issued`, else `dcterms:modified`. `SubmissionDate` (RO-Crate `dateCreated`) MUST stay empty.

#### Scenario: Issued date

- **WHEN** a dataset has `dcterms:issued` "2025-11-25T11:58:28"
- **THEN** the RO-Crate root `datePublished` MUST be "2025-11-25T11:58:28" and the root MUST NOT have `dateCreated`

#### Scenario: Only a modified date

- **WHEN** a dataset has no `dcterms:issued` and `dcterms:modified` "2026-01-02"
- **THEN** the RO-Crate root `datePublished` MUST be "2026-01-02"
