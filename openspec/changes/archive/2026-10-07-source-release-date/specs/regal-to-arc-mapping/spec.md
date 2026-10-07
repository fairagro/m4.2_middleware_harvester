## ADDED Requirements

### Requirement: Regal issued MUST be datePublished

`RegalMapper` MUST set Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`) from `dcterms:issued`.
`SubmissionDate` (RO-Crate `dateCreated`) MUST stay empty, since Regal has no creation date.

#### Scenario: Publisso record

- **WHEN** a record has `issued` "2024"
- **THEN** the RO-Crate root `datePublished` MUST be "2024" and the root MUST NOT have `dateCreated`
