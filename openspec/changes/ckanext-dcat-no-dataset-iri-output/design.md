# Design

## Context

See proposal.md. The `ckanext_dcat` mapper builds one Assay `Measurement` table per dataset from its distributions; the
`Output [URI]` value falls back to the dataset IRI when no distribution has an access or download URL.

## Goals / Non-Goals

**Goals:** `Output [URI]` only names data the source points to.

**Non-Goals:** blank-node datasets; the `Input [Source Name]` placeholder; a replacement output value.

## Decisions

- **Omit the column, not the table.** The table still carries the distribution title, format and licence comments, which
  are real source values; dropping the whole table would lose them. Same choice as `inspire-no-invented-output-uri`.
- **No other fallback (landing page, `dcterms:identifier`).** Those identify the metadata record, not the data, and the
  landing page is already exported through the `Landing Page` comment; an `Output [URI]` would only repeat it as a fake
  data entity.

## Risks / Trade-offs

- [A consumer reads `Output [URI]` as "the link" for every DCAT-AP ARC] → it must use the `Landing Page` comment, which
  every SRADI ARC has; the API export (#617) already reads that key.
