# Design

## Context

See proposal.md. Reproduced on `main`: with the space, `JsonLdParser` raises `JSON-LD produced an empty graph`;
without it the record parses.

## Goals / Non-Goals

**Goals:** the 3 PlabiPD records with whitespace in their DOI are harvested with a clean DOI.

**Non-Goals:** a general IRI repair for JSON-LD sources; the doubled `doi.org` resolver.

## Decisions

- **Repair in the PubPlant Protocol only.** It is a workaround for one provider's data defect; other sources should keep
  failing loudly so the defect is reported to them.
- **Remove all whitespace, not just spaces.** A DOI cannot contain whitespace, so no valid value changes.
- **Identity from the repaired record.** When PlabiPD fixes its data, the record then hashes to the same identifier and
  its ARC is updated instead of duplicated.

## Risks / Trade-offs

- [The identifier of the 3 records differs from a hash of the raw record] → they have never been harvested, so no
  published ARC changes identity; records without whitespace hash exactly as before.
