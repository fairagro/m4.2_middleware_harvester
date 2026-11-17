# Design

## Context

See proposal.md. Each of the three mappers resolves a URL for the Assay `Measurement` table and falls back to `""`
when none is found, then adds comment columns from the source. Since `linked-data-no-dataset-source-input`,
`Output [URI]` is the only column that is always present.

## Goals / Non-Goals

**Goals:** the Assay table only holds values from the source.

**Non-Goals:** changing how the URL is resolved; Regal's fail-closed behaviour.

## Decisions

- **Omit the column, no new fallback.** Same as US-006/US-010: a placeholder or derived identifier would be read as a
  resolvable URL.
- **Empty table → no table.** Without `Output [URI]` a record with no comments would yield a table with no columns;
  follow the INSPIRE rule and leave the Assay without an annotation table.

## Risks / Trade-offs

- [A consumer expects every Assay to have a table] → INSPIRE Assays can already be table-less.
