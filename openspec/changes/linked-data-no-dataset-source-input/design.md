# Design

## Context

See proposal.md. All four mappers build one Assay `Measurement` table per record with a hardcoded
`Input [Source Name]` cell, then add `Output [URI]` and comment columns from the source. This is the follow-up the
`inspire-dcat-no-dataset-source-input` change named as a non-goal.

## Goals / Non-Goals

**Goals:** the Assay table only holds values from the source.

**Non-Goals:** the `"Research Subject"` input of the MODS and PhenoROAM keyword tables; empty `Output [URI]` cells;
the `"Geographic Region"` source; ISA chaining.

## Decisions

- **Drop the column, don't replace it.** Same reasoning as `inspire-dcat-no-dataset-source-input`: no source value names
  the material the measurement started from.
- **No empty-table rule needed.** Unlike INSPIRE and DCAT-AP, these mappers always add `Output [URI]`, so the table keeps
  at least one column.

## Risks / Trade-offs

- [A consumer expects `LabProcess.object` to point at a Source] → the value never carried information; it was the same
  string in every ARC, and INSPIRE and DCAT-AP ARCs already ship without it.
