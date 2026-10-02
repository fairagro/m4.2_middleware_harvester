## ADDED Requirements

### Requirement: Publication authors MUST come from author-role contacts in initial-space-last form

`InspireMapper` MUST fill `Publication.authors` from Investigation contacts whose role is `author`, matched
case-insensitively (the CSW role `author` is stored as NCIT label `Author`), in contact order. Each author MUST be
formatted `F. Last` (or the single available name part) and joined by `; `, via the shared
`middleware.payload.person_contacts.publication_authors` helper also used by the Regal and Schema.org mappers. The
`Last, F.` form MUST NOT be used, because the RO-Crate writer splits `Publication.authors` on `,`.

#### Scenario: Author role is matched despite the NCIT label

- **WHEN** a record has a contact `John Doe` with role `author` and a DOI resource identifier
- **THEN** the DOI Publication MUST have authors `J. Doe`

#### Scenario: Several authors survive RO-Crate serialization

- **WHEN** a record has author contacts `John Doe` and `Rita Roe` and a DOI resource identifier
- **THEN** the Publication authors MUST be `J. Doe; R. Roe`, and the RO-Crate MUST contain exactly one `#Author_*` node,
  `#Author_J. Doe; R. Roe`
