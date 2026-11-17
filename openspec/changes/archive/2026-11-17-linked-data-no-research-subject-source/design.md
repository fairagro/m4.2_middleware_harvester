# Design

## Context

See proposal.md. This is the non-goal the `linked-data-no-dataset-source-input` change named for the keyword tables,
widened to schema.org and Regal, which carry the same literal.

## Goals / Non-Goals

**Goals:** the Data Collection table only holds values from the source.

**Non-Goals:** empty `Output [URI]` cells; the `"Geographic Region"` source; ISA chaining.

## Decisions

- **Drop both columns, don't replace them.** No source value names the material or the resulting sample; the cells were
  the same string (or empty) in every ARC.
- **No empty-table rule needed.** The table is only built when at least one parameter has a value. A probe shows arctrl
  serialises a parameter-only table as a `LabProcess` with `object: []`, `result: []` and the parameter values intact.

## Risks / Trade-offs

- [A consumer reads keywords via the process input/output] → keywords live in the `Keywords` parameter value, which is
  unchanged; the manual dump diff checks they still reach the API.
