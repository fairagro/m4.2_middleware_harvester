# Design

## Context

See proposal.md. The schema.org and MODS mappers resolve a URL for the Assay `Measurement` table and fall back to `""`
when none is found, then add comment columns from the source. Since `linked-data-no-dataset-source-input`,
`Output [URI]` is the only column that is always present.

PhenoROAM has the same fallback, but its catalog id comes from `itemUUID` or the harvest source id, and a record with
neither is refused when the Investigation identifier is resolved. The fallback can never run.

## Goals / Non-Goals

**Goals:** the Assay table only holds values from the source.

**Non-Goals:** changing how the URL is resolved; Regal's fail-closed behaviour.

## Decisions

- **Omit the column, no new fallback.** Same as US-006/US-010: a placeholder or derived identifier would be read as a
  resolvable URL.
- **Empty table → no table.** Without `Output [URI]` a record with no comments would yield a table with no columns;
  follow the INSPIRE rule and leave the Assay without an annotation table.
- **PhenoROAM: remove the dead fallback, no spec delta, no test.** There is no input that reaches the branch through
  `map()` or `map_record()`, so there is no behaviour to specify or pin; the existing URL-present test keeps the cell
  covered.

## Risks / Trade-offs

- [A consumer expects every Assay to have a table] → INSPIRE Assays can already be table-less.
