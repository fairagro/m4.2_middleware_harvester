---
payload_kind: rdf_graph
mapper_id: ckanext_dcat
---

# CKAN ckanext-dcat (DCAT-AP) to ARC Mapping Documentation

This document describes how DCAT-AP RDF graphs in the CKAN `ckanext-dcat` flavour (one `dcat:Dataset` per mapped graph)
are mapped to the ISA (Investigation, Study, Assay) model used by ARC.

**Related specs:**

- Implementation contract:
  [`openspec/specs/ckanext-dcat-to-arc-mapping/`](../../openspec/specs/ckanext-dcat-to-arc-mapping/)
- Protocol: [`openspec/specs/dcat-ap-protocol/`](../../openspec/specs/dcat-ap-protocol/)

> [!NOTE] Nothing RDI-specific is hardcoded. Catalog provenance comes from repository `mapper.catalog_name` /
> `mapper.catalog_url`. Field access uses StableGraph / ResourceView; this document speaks DCAT-AP / DCTERMS / FOAF /
> vCard predicates, not StableGraph APIs.

## Concept

One `dcat:Dataset` subject → one Investigation with Study `{id}_study` and Assay `{id}_assay`. Graphs without a
`dcat:Dataset` are rejected.

Namespaces: `dcat:` (`http://www.w3.org/ns/dcat#`), `dcterms:`, `foaf:`, `vcard:`.

## Identity

| Source field / config             | Description                   | ARC Mapping                                                                                   |
| --------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------- |
| **Dataset subject IRI**           | `dcat:Dataset` node           | `Investigation.Identifier` (sanitized IRI); fallback slug of title; fail closed if both empty |
| **`dcterms:title`**               | Dataset title                 | `Investigation.Title` / Study / Assay title; required — fail closed if missing                |
| **`mapper.catalog_name` / `url`** | Repository catalog provenance | `Investigation.Comment("Data Catalog")` — `Name (URL)`, or either alone when only one is set  |

## Investigation

| Source field              | Description            | ARC Mapping                                                              |
| ------------------------- | ---------------------- | ------------------------------------------------------------------------ |
| **`dcterms:title`**       | Title                  | `Investigation.Title`                                                    |
| **`dcterms:description`** | Description            | `Investigation.Description` (empty string when absent)                   |
| **`dcterms:issued`**      | Issue date             | `Investigation.PublicReleaseDate` (else `dcterms:modified`)              |
| **`dcterms:identifier`**  | Source identifier      | `Investigation.Comment("Source Identifier")`                             |
| **`dcterms:modified`**    | Modified date          | `Investigation.Comment("Modified")`                                      |
| **`dcat:keyword`**        | Keywords               | `Investigation.Comment("Keywords")` (semicolon-joined)                   |
| **`dcterms:language`**    | Languages              | `Investigation.Comment("Language")` (semicolon-joined)                   |
| **`dcterms:publisher`**   | Publisher org          | `Investigation.Comment("Publisher")` via `foaf:name` (see Org labels)    |
| **`dcat:contactPoint`**   | Contact                | `Investigation.Comment("Contact Point")` via `vcard:fn` (see Org labels) |
| **`dcterms:spatial`**     | Spatial extent present | `Investigation.Comment("Spatial Extent")` fixed text pointing at the RDI |
| **(config) Data Catalog** | Catalog name/URL       | `Investigation.Comment("Data Catalog")`                                  |
| **(fixed)**               | Ontology source        | `OntologySourceReferences` entry for DCAT                                |

**Contacts.** `Investigation.Contacts` stays empty today (ckanext-dcat exposes org-level publisher/contactPoint only).
`require_nonempty_person_given_names` still runs for parity / future Person creators.

## Study

| Source field            | Description  | ARC Mapping                                                                                                                                                                                                                                          |
| ----------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title / description     | From dataset | `Study.Title` / `Study.Description`; `Study.Identifier` = `{investigation_id}_study`                                                                                                                                                                 |
| **`dcterms:issued`**    | Issue date   | `Study.PublicReleaseDate` (else `dcterms:modified`)                                                                                                                                                                                                  |
| (fixed + keywords/lang) | Processing   | Table `Dataset Processing`: Input Raw Data → Parameter `Processing Description` = “Published dataset metadata harvested via DCAT-AP.” → Output Data “Published Dataset”; optional `Keywords` (`", "`-joined) / `Language` (`"; "`-joined) parameters |

## Assay

| Source field                       | Description      | ARC Mapping                                                                                           |
| ---------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------- |
| Title                              | From dataset     | `Assay.Title`; identifier `{investigation_id}_assay`                                                  |
| (fixed)                            | Types / platform | measurement Data Collection; technology Data Repository; platform `DCAT-AP Catalog`                   |
| **`dcat:distribution`**            | Distributions    | Table `Measurement`: `Output [URI]` = first `dcat:accessURL` or `dcat:downloadURL`, else dataset IRI  |
| Distribution **`dcterms:title`**   | Titles           | `Comment("Distribution Title")` (semicolon-joined)                                                    |
| Distribution **`dcterms:format`**  | Formats          | `Comment("Format")` (unique, sorted, semicolon-joined)                                                |
| Distribution access/download URLs  | URLs             | `Comment("Access URL")`: per distribution `dcat:accessURL`, else `dcat:downloadURL`; semicolon-joined |
| Distribution **`dcterms:license`** | Licenses         | `Comment("License")` (unique, sorted, semicolon-joined)                                               |

## Org labels (publisher / contact)

Literals on `foaf:name` / `vcard:fn` may be plain text or raw CKAN JSON strings (bare object or single-element array)
with keys `maintainer_name` / `author_name` / `name` and `maintainer_email` / `author_email` / `email`.

| Input shape                                        | Mapped label     |
| -------------------------------------------------- | ---------------- |
| Plain string                                       | verbatim         |
| `{"maintainer_name":"A","maintainer_email":"a@x"}` | `A <a@x>`        |
| `[{"author_name":"A","author_email":"a@x"}]`       | `A <a@x>`        |
| JSON without recognized name keys / invalid JSON   | original literal |

## Fallbacks

1. **Title:** `dcterms:title` only — mapping fails closed if missing (never `"Untitled"`).
2. **Identifier:** sanitized dataset IRI → title slug; fail closed if both empty (never `untitled`).
3. **Assay Output URI:** first distribution access/download URL → dataset IRI string.
4. **Catalog comment:** `name (url)` → name only → url only → omit.

## Refusal / skip rules

| Condition                                      | Behaviour                      |
| ---------------------------------------------- | ------------------------------ |
| No `dcat:Dataset` in the graph                 | `ValueError`                   |
| Missing `dcterms:title`                        | `ValueError` (no `"Untitled"`) |
| Missing optional DCAT fields                   | Omitted comments / columns     |
| Blank `catalog_name` / `catalog_url` in config | Treated as unset               |
