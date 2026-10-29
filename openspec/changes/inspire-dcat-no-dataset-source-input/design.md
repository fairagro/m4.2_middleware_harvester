# Design

## Context

See proposal.md. Both mappers build one Assay `Measurement` table per record with a hardcoded `Input [Source Name]`
cell, then add `Output [URI]` and comment columns from the source.

## Goals / Non-Goals

**Goals:** the Assay table only holds values from the source.

**Non-Goals:** the other mappers using the same literal; the Study `Geographic Region` source; ISA chaining from the
Study sample to the Assay.

## Decisions

- **Drop the column, don't replace it.** No source value names the material the measurement started from. A record
  identifier would only repeat the Investigation identifier as a fake sample.
- **Omit an empty table.** Without the Input column a record with no URI and no comments would give a zero-column table.
  An Assay without an annotation table says the same thing without an empty `LabProcess`.

## Risks / Trade-offs

- [A consumer expects `LabProcess.object` to point at a Source] → the value never carried information; it was the same
  string in every ARC.
