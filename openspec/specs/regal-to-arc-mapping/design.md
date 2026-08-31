# Regal-to-ARC Mapping — Design

## Architecture overview

A `RegalMapper` (name illustrative) implements `LinkedDataMapper` for
`PayloadType.regal_general`. It consumes an `rdflib.Graph` produced by the Regal dataset
strategy and builds ARC objects with arctrl according to
[docs/regal_mapping.md](../../../docs/regal_mapping.md).

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

5. **Person contacts require non-empty FirstName; org-style labels are not empty-given Persons**
   — `prefLabel` without `", "` must not become `Person(first_name="")`. Organizational/
   label-only agents become Investigation comments; ORCID agents without a given name fail
   closed. Institutions continue via Affiliation / Institution comments (see
   `docs/regal_mapping.md` and `person-contact-given-name`).

6. **Opaque Comments never embed rdflib blank-node labels**
   — Unlabelled blank nodes are skipped; Literals, URIRefs, and `skos:prefLabel` remain.
   `regal:contributorOrder` is known metadata (not an opaque Comment); Contact ordering
   via that predicate is deferred until stable order keys are available.

7. **ARC-bound RDF reads go through StableGraph / ResourceView**
   — Per-call `_RegalRun` wraps the graph with `label_predicates=(skos:prefLabel,)`.
   Private `_str` / `_strs` / `_labelled_nodes` helpers are not used. Multi-value,
   contact, and opaque-comment order is harvest-stable under RDF permutation.
   Regal ARC policy (joinedFunding preference, PUBLISSO name split, resource base
   URL) stays mapper-local — see `openspec/specs/stable-graph/`.
