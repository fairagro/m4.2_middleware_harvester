# Proposal

## Why

One of the 2,335 PlabiPD `genomes.json` records repeats the DOI resolver: `@id` is
`https://doi.org/doi.org/10.1093/dnares/dsx047` and `identifier` is `doi.org/10.1093/dnares/dsx047`. The record parses,
but `normalize_doi` strips `https://doi.org/` once and is left with a scheme-less `doi.org/10.1093/…`, which is not a
DOI. The ARC therefore carries no publication DOI, and its `Output [URI]` is the doubled URL, which returns HTTP 404.
The provider fix is requested in the PlabiPD metadata feedback; until then this genome is a DOI-less catalogue entry
with a dead link.

## What Changes

- The `pubplant_json_array` Protocol collapses a stack of DOI resolver prefixes (`doi.org/`, `dx.doi.org/`,
  `www.doi.org/`, with or without `http(s)://`) at the start of the top-level `@id` and DOI-like `identifier` strings of
  each record: `@id` becomes `https://doi.org/<doi>` and `identifier` the bare `<doi>`. One WARNING per repaired record
  names the original values.
- The record identifier and content hash are computed from the repaired record, so the provider's own fix later keeps
  the same identifier.
- **Non-goals:** a scheme-less `doi.org/` prefix in the shared `normalize_doi` (all sources); other fields (`url`,
  `sameAs`, …); any other Protocol.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `pubplant-json-array-protocol`: doubled DOI resolvers are collapsed; identity is computed from the repaired record.

## Impact

- `middleware/generic` `pubplant_json_array` Protocol and its tests.
- PlabiPD: the one doubled record's ARC carries `10.1093/dnares/dsx047` and a working link, and gets a new identifier
  once; all other records keep their identifiers and payloads.
