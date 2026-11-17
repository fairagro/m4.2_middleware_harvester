# Spec Delta

## ADDED Requirements

### Requirement: Data Collection table MUST NOT invent a source or sample

The Regal Study `Data Collection` table MUST NOT contain an `Input [Source Name]` or an `Output [Sample Name]` column,
because no source field names the material studied or the sample produced. Its parameter columns (`Keywords`,
`Data Origin`, `Temporal Extent`) MUST be unchanged, and the table MUST still be omitted when the record has no value
for any of them.

#### Scenario: Record with keywords, a data origin or a recording period mapped without invented samples

- **GIVEN** a Regal record with keywords, a data origin or a recording period
- **WHEN** it is mapped
- **THEN** the `Data Collection` table has no `Input [Source Name]` or `Output [Sample Name]` column, the RO-Crate
  `@graph` has no `#Source_Research_Subject` or `#Sample_` entity, and its parameter columns (`Keywords`, `Data Origin`,
  `Temporal Extent`) keep their values

#### Scenario: Record without those fields has no Data Collection table

- **GIVEN** a Regal record with no keywords, data origin or recording period
- **WHEN** it is mapped
- **THEN** the Study has no `Data Collection` table
