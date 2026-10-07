## ADDED Requirements

### Requirement: Regal isDescribedBy.modified MUST be dateModified

`RegalMapper` MUST add the Investigation Comment `dateModified` (RO-Crate root `dateModified`) from `ore:isDescribedBy`
→ `dcterms:modified`, normalised by `iso_date`. Without it there MUST be no `dateModified`.

#### Scenario: Publisso record

- **WHEN** a record has `isDescribedBy.modified` "2024-09-04T09:34:30.938+0200"
- **THEN** the RO-Crate root `dateModified` MUST be "2024-09-04T09:34:30.938+0200"
