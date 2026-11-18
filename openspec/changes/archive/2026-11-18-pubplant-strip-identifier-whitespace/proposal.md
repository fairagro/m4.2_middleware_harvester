# Proposal

## Why

Three of the 2,335 PlabiPD `genomes.json` records have a space after the DOI prefix in `@id` and `identifier`
(`https://doi.org/10.1038/ s41597-026-06582-z`, `10.1038/ s41597-026-06561-4`, `10.3390/ ijms23137039`). rdflib drops a
node whose `@id` is not a valid IRI, so each record parses to an empty graph and is reported as failed. The provider fix
is requested in the PlabiPD metadata feedback; until then these genomes are missing from the catalogue.

## What Changes

- The `pubplant_json_array` Protocol removes every whitespace character from the top-level `@id` and `identifier`
  strings of each record before identity is computed and the record is yielded, and logs one WARNING per repaired record
  with the original value.
- The record identifier and content hash are computed from the repaired record, so the provider's own fix later keeps
  the same identifier.
- **Non-goals:** the doubled resolver `https://doi.org/doi.org/…` (valid IRI, separate card); whitespace in other fields
  (`url`, `sameAs`, …); whitespace repair for any other Protocol or the shared JSON-LD parser.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `pubplant-json-array-protocol`: identifier whitespace is repaired; identity is computed from the repaired record.

## Impact

- `middleware/generic` `pubplant_json_array` Protocol and its tests.
- PlabiPD: the 3 failing records are harvested; all other records keep their identifiers and payloads.
