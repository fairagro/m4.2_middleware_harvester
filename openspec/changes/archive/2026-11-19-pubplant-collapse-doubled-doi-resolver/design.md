# Design

## Context

See proposal.md. Reproduced on `main` (106da6f3) through `GenericPlugin`: the record is harvested with
`Publications == []`, `Output [URI] = https://doi.org/doi.org/10.1093/dnares/dsx047` and identifier
`doi_org_doi_org_10_1093_dnares_dsx047:<hash>`.

## Goals / Non-Goals

**Goals:** the PlabiPD record with a doubled resolver carries its DOI and a resolving link.

**Non-Goals:** a general DOI repair for all sources; changing `normalize_doi`.

## Decisions

- **Repair in the PubPlant Protocol only**, next to the whitespace repair. It is a workaround for one provider's data
  defect; other sources keep surfacing such defects so they are reported to them.
- **Collapse any stack of resolver prefixes**, with or without a scheme, so `doi.org/…` and
  `https://dx.doi.org/https://doi.org/…` are handled the same way; a value that is not a DOI after collapsing is left
  unchanged.
- **Keep the record's own shape.** `@id` stays a resolver URL (`https://doi.org/<doi>`), `identifier` stays a bare DOI,
  as in the other records.
- **Identity from the repaired record.** When PlabiPD fixes its data, the record hashes to the same identifier and its
  ARC is updated instead of duplicated.

## Risks / Trade-offs

- [The doubled record's published ARC changes identifier once] → one ARC, already wrong (no DOI, dead link); records
  without a doubled resolver hash exactly as before.
