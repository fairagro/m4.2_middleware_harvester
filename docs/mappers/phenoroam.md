---
payload_kind: phenoroam_record
mapper_id: phenoroam_general
---

# PhenoRoam to ARC Mapping Documentation

This document describes how typed PhenoRoam intermediate records (`PayloadKind.phenoroam_record`, parsed from PhenoRoam
XML / `pr:` vocabulary) are mapped to the ISA (Investigation, Study, Assay) model used by ARC.

**Related specs:**

- Implementation contract: [`openspec/specs/phenoroam-to-arc-mapping/`](../../openspec/specs/phenoroam-to-arc-mapping/)
- Given-name policy: [`openspec/specs/person-contact-given-name/`](../../openspec/specs/person-contact-given-name/)

> [!NOTE] The mapper consumes a typed `PhenoroamRecord`, not RDF. Source field names below are the intermediate model
> attributes (filled by the PhenoRoam parser from `pr:` blocks). Mapping is direct PhenoRoam → ARC — not via Schema.org.

## Concept

One PhenoRoam metadata dataset → one Investigation with one Study and one Assay. Harvests are **metadata-only**: remote
datafile links MUST NOT become fabricated ISA Data File / Output entities.

Landing-page template used when an identifier or comment needs a catalog URL:

`https://phenoroam.phenorob.de/geonetwork/srv/eng/catalog.search#/metadata/{id}`

## Identity

| Source field / context                     | Description                 | ARC Mapping                                                                                           |
| ------------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------- |
| **`item_uuid`**                            | Unique item UUID            | `Investigation.Identifier` (sanitized) when non-empty after trim                                      |
| **`harvest_source_id` / OAI id** (context) | Catalog id when UUID absent | Landing-page URL → `Investigation.Identifier` (sanitized); also used for landing comments / assay URI |
| **`source_url`** (context, http(s) only)   | Discovery URL               | `HarvestedArc.source_url` when absolute http(s); else landing URL from catalog id                     |

**Refusal.** Mapping fails if there is no investigation/dataset title (see Investigation) or neither `item_uuid` nor a
catalog id is available for the landing-URL identifier fallback. A DOI is **not** required.

## Investigation

| Source field                          | Description                       | ARC Mapping                                                     |
| ------------------------------------- | --------------------------------- | --------------------------------------------------------------- |
| **`study.investigation_title`**       | Nested investigation title        | `Investigation.Title` (preferred when non-empty)                |
| **`title`**                           | Dataset title                     | `Investigation.Title` fallback                                  |
| **`study.investigation_description`** | Nested investigation description  | `Investigation.Description` (preferred when set)                |
| **`description`**                     | Dataset description               | `Investigation.Description` fallback                            |
| **`md_change_date`**                  | Metadata change date              | `Investigation.SubmissionDate`                                  |
| **`item_uuid` / catalog id**          | Catalog identity                  | `Investigation.Comment("Landing Page")` → landing URL           |
| **`how_to_cite`**                     | Citation text                     | `Investigation.Comment("How To Cite")`                          |
| **`funded_by`**                       | Funding note                      | `Investigation.Comment("Funded By")`                            |
| **`download_information`**            | Download instructions             | `Investigation.Comment("Download Information")`                 |
| **`core_projects`**                   | Project names                     | one `Investigation.Comment("Core Project")` per non-empty entry |
| **`thumbnail_url`**                   | Thumbnail (http(s) with hostname) | `Investigation.Comment("Thumbnail")` when URL validates         |

## Study

| Source field                  | Description       | ARC Mapping                                                                            |
| ----------------------------- | ----------------- | -------------------------------------------------------------------------------------- |
| **`study.study_title`**       | Study title       | `Study.Title` (else `title`, else `"PhenoRoam Study"`)                                 |
| **`study.study_description`** | Study description | `Study.Description` (else `description`)                                               |
| Study title (slug)            | Study identifier  | `Study.Identifier` = slug of study title, or `phenoroam_study`                         |
| **`keywords`**                | Keyword list      | Study table `Data Collection`: Parameter `Keywords` (comma-joined); omitted when empty |

## Assay

| Source field / context   | Description                   | ARC Mapping                                                                                             |
| ------------------------ | ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| **`title`** / inv. title | Assay title                   | `Assay.Title`; identifier slug of title or `phenoroam_assay`                                            |
| (fixed)                  | Measurement / technology      | `measurement_type` = Data Collection; `technology_type` = Data Repository; platform = PhenoRoam         |
| Landing URL              | Catalog landing page          | Assay table `Measurement` `Output [URI]`                                                                |
| **`license_text`**       | License / rights text         | Assay table `Comment("License")` (whitespace collapsed)                                                 |
| **`datafile_links`**     | Remote file URLs (`itemLink`) | Assay table `Comment("Datafile Link")` — valid http(s) URLs joined with `;` — **not** Data File Outputs |
| **`bbox`**               | Geographic bounding box       | Assay table `Comment("Geographic Bounding Box")` as `W:… E:… S:… N:…` when any side present             |

Empty-port URLs such as `https://host:/path` are accepted (PhenoRoam fixture shape).

## Contacts

Contacts come from `responsible_contacts` then `other_contacts` (`pr:blockPerson`).

| Source field      | Description  | ARC Mapping                                                             |
| ----------------- | ------------ | ----------------------------------------------------------------------- |
| **`name`**        | Display name | Split via `split_display_name` → `Person.FirstName` / `Person.LastName` |
| **`email`**       | Email        | `Person.Email`                                                          |
| **`affiliation`** | Affiliation  | `Person.Affiliation` (empty string when absent)                         |

Blank names are skipped. A name that yields no given name fails closed (`ValueError`), then
`require_nonempty_person_given_names` enforces the shared given-name policy on the Investigation.

## Fallbacks

1. **Title:** `study.investigation_title` → `title` → error.
2. **Description:** `study.investigation_description` → `description`.
3. **Identifier:** sanitized `item_uuid` → sanitized landing URL from catalog id → error.
4. **HarvestedArc.source_url:** context `source_url` if http(s) → else landing URL from catalog id.

## Refusal / skip rules

| Condition                                        | Behaviour                                       |
| ------------------------------------------------ | ----------------------------------------------- |
| Wrong `PayloadKind` / value type                 | `ValueError` / `TypeError`                      |
| No investigation or dataset title                | `ValueError`                                    |
| No `item_uuid` and no catalog id for landing URL | `ValueError`                                    |
| Person name without given name after split       | `ValueError` (fail closed)                      |
| Datafile links present                           | Mapping still succeeds; links are comments only |
