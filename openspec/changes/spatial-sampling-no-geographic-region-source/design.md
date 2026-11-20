# Design

## Context

See proposal.md. This is the non-goal the `inspire-dcat-no-dataset-source-input`, `linked-data-no-dataset-source-input`
and `linked-data-no-research-subject-source` changes named for the Spatial Sampling tables, widened to PhenoROAM, which
carries the same literal.

## Goals / Non-Goals

**Goals:** the Spatial Sampling table only holds values from the source, plus the existing `Selected Location` chain.

**Non-Goals:** the `Selected Location` output; the Regal empty Data Collection output; ISA chaining beyond the existing
INSPIRE Spatial Sampling → Data Acquisition link (#353).

## Decisions

- **Drop the input, don't replace it.** No source field names a source material; the region is already described by the
  spatial parameters, and a region is not a sample.
- **Keep the `Selected Location` output.** INSPIRE Data Acquisition consumes it (`inspire-to-arc-mapping`, "No dangling
  Selected Location"); Regal and PhenoROAM keep it for consistency until the output itself is decided.

## Risks / Trade-offs

- [A consumer reads the region via the process input] → the region values live in the parameter values, which are
  unchanged; the manual dump diff checks they still reach the API.
