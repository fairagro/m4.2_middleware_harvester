# Regal-to-ARC Mapping — Design

## Architecture overview

A `RegalMapper` (name illustrative) implements `LinkedDataMapper` for
`PayloadType.regal_general`. It consumes an `rdflib.Graph` produced by the Regal dataset
strategy and builds ARC objects with arctrl according to
[docs/regal_mapping.md](../../../../docs/regal_mapping.md).

```text
Regal JSON-LD → Graph → RegalMapper.map_graph()
  ├── ArcInvestigation (identity, contacts, publications, comments)
  ├── ArcStudy (Spatial Sampling?, Data Collection?, Data Processing)
  └── ArcAssay (Measurement table → Output [URI])
        └── ToROCrateJsonString()
```

## Key Decisions

1. **Authoritative rules live in `docs/regal_mapping.md`**
   — Same pattern as INSPIRE (`docs/inspire_mapping.md`). Feature specs state the
   implementation contract; they do not duplicate field tables.

2. **Dedicated Regal mapper, not `GeneralSchemaOrgMapper`**
   — Regal predicates are DC/SKOS/Regal, not schema.org. Reusing the schema.org
   mapper would require a lossy intermediate crosswalk.

3. **Conditional Spatial Sampling**
   — Most FRL research-data records are non-spatial. Creating an empty spatial
   protocol would add noise; omit it unless coordinates or location exist.

4. **Prefer DOI landing URLs for Assay `Output [URI]`**
   — DOIs are the stable public identifier; the repository resource URL remains
   the fallback when no DOI is present.
