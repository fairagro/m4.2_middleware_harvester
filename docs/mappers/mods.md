---
payload_kind: mods_record
mapper_id: mods_general
---

# MODS to ARC Mapping Documentation

This document describes how typed MODS intermediate records (`PayloadKind.mods_record`, parsed from MyCoRe object XML
via `mods_xml`) are mapped to the ISA (Investigation, Study, Assay) model used by ARC.

**Related specs:**

- Implementation contract: [`openspec/specs/mods-to-arc-mapping/`](../../openspec/specs/mods-to-arc-mapping/)
- Given-name policy: [`openspec/specs/person-contact-given-name/`](../../openspec/specs/person-contact-given-name/)

> [!NOTE] The mapper consumes a typed `ModsRecord`, not RDF. Source field names below are intermediate model attributes
> filled by the MODS parser from `mods:` elements (and MyCoRe envelope fields such as `maindoc`). Mapping is direct MODS
> → ARC.

## Concept

One MODS research-data object → one Investigation with one Study and one Assay. Harvests are **metadata-only**: derivate
`maindoc` filenames become assay comments, not fabricated ISA Data File / Output entities.

Primary production path: `generic` → `mycore_rest` → `mods_xml` → `mods_general` (e.g. OpenAgrar).

## Identity

| Source field / context                    | Description      | ARC Mapping                                                                                            |
| ----------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------ |
| **`harvest_source_id`** / **`object_id`** | MyCoRe object id | `Investigation.Identifier` (sanitized) — preferred so existing OpenAgrar ARCs update in place          |
| **`doi`** (`mods:identifier[@type=doi]`)  | Dataset DOI      | Identifier fallback when object id absent; always also `Publications[]` when present                   |
| **`source_url`** (context, http(s) only)  | Landing page URL | Identifier fallback when object id and DOI absent; also `HarvestedArc.source_url` / Source URL comment |

Discovery for MyCoRe REST yields `/receive/{id}` as the landing `source_url` and sets `fetch_url` to
`/api/v2/objects/{id}` for the parser fetch only.

**Refusal.** Mapping fails if there is no title, or none of object id / DOI / http(s) source URL can form an
Investigation identifier.

## Investigation

| Source field                                               | Description               | ARC Mapping                                                                               |
| ---------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| **`title`** (`mods:titleInfo/mods:title` with text)        | Dataset title             | `Investigation.Title`                                                                     |
| **`abstract`** (`mods:abstract` with text)                 | Description               | `Investigation.Description`                                                               |
| **`date_issued`** (`mods:originInfo/mods:dateIssued`)      | Publication / issued date | `SubmissionDate` and `PublicReleaseDate`                                                  |
| **`doi`**                                                  | DOI                       | `Publications[]` with bare DOI                                                            |
| **`language`**                                             | Language code             | `Comment("Language")`                                                                     |
| **`license_uri`** (`accessCondition` use and reproduction) | Licence URI               | `Comment("License")` (raw); `ARC.License` uses CC deed URL when `mir_licenses#…` is known |
| **`source_url`**                                           | Landing page URL          | `Comment("Source URL")`                                                                   |

Empty `titleInfo` / `abstract` nodes that only carry `altFormat` base64 companions are ignored in favour of siblings
with element text.

## Study

| Source field   | Description | ARC Mapping                                                        |
| -------------- | ----------- | ------------------------------------------------------------------ |
| **`title`**    | Study title | `Study.Title` (same as investigation title)                        |
| **`abstract`** | Description | `Study.Description`                                                |
| Title slug     | Identifier  | `Study.Identifier` = slug of title, or `mods_study`                |
| **`keywords`** | Topics      | Study table `Data Collection`: Parameter `Keywords` (comma-joined) |

## Assay

| Source field / context | Description              | ARC Mapping                                                                                |
| ---------------------- | ------------------------ | ------------------------------------------------------------------------------------------ |
| **`title`**            | Assay title              | `Assay.Title`; identifier slug of title or `mods_assay`                                    |
| (fixed)                | Measurement / technology | `measurement_type` = Data Collection; `technology_type` = Data Repository; platform = MODS |
| **`source_url`**       | Landing page URL         | Assay table `Measurement` `Output [URI]`                                                   |
| **`license_uri`**      | Licence URI              | Assay table `Comment("License")`                                                           |
| **`datafile_names`**   | Derivate `maindoc` names | Assay table `Comment("Datafile Name")` joined with `;` — **not** Outputs                   |

## Contacts

Contacts come from `mods:name` (typically `type="personal"`).

| Source field                       | ARC Mapping                                                         |
| ---------------------------------- | ------------------------------------------------------------------- |
| **`namePart[@type=given/family]`** | `Person` first/last name (preferred)                                |
| **`displayForm`**                  | Split via shared display-name helper when given/family parts absent |
| **`affiliation`**                  | `Person.affiliation`                                                |
| **`nameIdentifier[@type=orcid]`**  | `Person.orcid`                                                      |
| **`nameIdentifier[@type=gnd]`**    | `Person.Comment("GND")`                                             |

**Refusal.** A mapped person without a non-empty given name fails closed (person-contact-given-name policy).

## Fallbacks

- Title: first `mods:titleInfo` that has a non-empty `mods:title` text node.
- Abstract: first `mods:abstract` with non-empty text (skip altFormat-only companions).
- Licence: `mods:accessCondition[@type="use and reproduction"]/@xlink:href`, else element text.
- Identifier: harvest_source_id / object id → DOI → source URL (see Identity).

## Refusal / skip rules

- No title → mapping error (fail closed; no `Untitled`).
- No DOI, object id, or http(s) source URL → mapping error.
- Person without given name → mapping error.

## Source placeholders

`mapper.placeholders` treats configured sentinel strings as absent for licence values (same contract as linked-data
mappers).
