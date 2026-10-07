---
payload_kind: rdf_graph
mapper_id: schema_org_general
---

# Schema.org to ARC Mapping Documentation

This document describes how Schema.org RDF graphs (parsed from JSON-LD embedded in HTML pages or inline in API
responses) are mapped to the ISA (Investigation, Study, Assay) model used by ARC.

**Related specs:**

- Implementation contract: [`openspec/specs/schemaorg-to-arc-mapping/`](../../openspec/specs/schemaorg-to-arc-mapping/)

## Concept

Schema.org metadata describes published datasets, while ARC describes the research process. We reconstruct a minimal ISA
workflow that preserves provenance: one `schema:Dataset` → one Investigation with one Study and one Assay. A single page
may contain multiple Dataset entities (e.g. DataCatalog with `hasPart`), each producing a separate Investigation.

### Protocol-Based Mapping Philosophy

> [!IMPORTANT] **Protocols are central to ARC**: They describe exactly how data was created. Since Schema.org metadata
> rarely encodes laboratory steps, we model publication as process:
>
> - **Data Collection** — keywords, research subject (single-row protocol stub)
> - **Data Processing** — repository publication, license, publisher context
> - **Measurement** — dataset landing page URL, distribution file access
>
> Dataset `schema:description` maps to `Investigation.Description` / `Study.Description` only — it is not duplicated as
> a Data Collection parameter.

### Scope

| In scope                                                                                | Out of scope                                                  |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `schema:Dataset` entities with `@type` in `http://schema.org/` or `https://schema.org/` | Non-Dataset types (`schema:Software`, `schema:Article`, etc.) |
| JSON-LD embedded in HTML or inline API responses                                        | JSON-LD with unknown `@context` (validated before parsing)    |
| `schema:DataDownload` distributions                                                     | External file downloads not linked via `schema:distribution`  |

## Available Schema.org Metadata Fields

Fields below use Schema.org terminology. The mapper supports both `http://schema.org/` and `https://schema.org/`
namespaces (dual-namespace aliasing via `StableGraph`).

### 1. Dataset Identity and Type

| Schema.org Field                 | Description                             | ARC Mapping                                                                                                                                                                   |
| -------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`@id`**                        | Subject IRI (blank node or HTTP(S) URI) | `Investigation.Identifier` (when no higher-precedence ID); see [Identifier Cascade](#identifier-cascade-precedence)                                                           |
| **`@type`**                      | Must be `schema:Dataset`                | Gate: only Dataset entities are mapped; `DataCatalog` is container, not output                                                                                                |
| **`schema:name`**                | Dataset title                           | `Investigation.Title`, `Study.Title`, `Assay.Title`; falls back to `headline` / `alternativeHeadline` / page title, see [Title Resolution Cascade](#title-resolution-cascade) |
| **`schema:headline`**            | Dataset title (fallback)                | Title fallback when `schema:name` is missing or blank; adds `Investigation.Comment("Title Source")`                                                                           |
| **`schema:alternativeHeadline`** | Alternative titles (fallback)           | Title fallback after `headline`; first non-empty entry in **casefold-alphabetical order**                                                                                     |
| **`schema:description`**         | Abstract / summary                      | `Investigation.Description`, `Study.Description`                                                                                                                              |
| **`schema:url`**                 | Canonical landing page URL              | `Investigation.Identifier` (sanitized); Assay `Output [URI]`                                                                                                                  |
| **`schema:sameAs`**              | Equivalent URLs                         | `Investigation.Identifier` fallback (lexicographic min)                                                                                                                       |
| **`schema:identifier`**          | DOI, URL, or other identifiers          | `Investigation.Identifier` (DOI as last resort); Publication DOI; `Investigation.Comment("Alternate Identifier")`                                                             |
| **`schema:datePublished`**       | Publication date                        | `Investigation.PublicReleaseDate`, `Study.PublicReleaseDate` (RO-Crate `datePublished`), ISO 8601 (see Dates below)                                                           |
| **`schema:dateModified`**        | Last modification date                  | Investigation Comment `dateModified` (RO-Crate root `dateModified`, ISO 8601); also `PublicReleaseDate` when `datePublished` is missing or not a date                         |
| **`schema:dateCreated`**         | Creation date                           | `Investigation.SubmissionDate`, `Study.SubmissionDate` (RO-Crate `dateCreated`); also `PublicReleaseDate` when neither other date is usable                                   |

**Dates.** Values go through `middleware.payload.iso_dates.iso_date`: ISO 8601 dates and date-times (`2011`,
`2011-01-01`, `2011-01-01T10:00:00Z`) pass unchanged; Java `Date.toString()` values (e!DAL:
`Sat Jan 01 00:00:00 CET 2011`) become `2011-01-01T00:00:00+01:00` (local day kept, offset from the zone abbreviation)
with a warning. Anything else is never written as a date: it is logged and kept as the Investigation Comment
`Unparsed datePublished` / `Unparsed dateModified` / `Unparsed dateCreated`. `PublicReleaseDate` falls back to
`dateModified`, then `dateCreated`: left empty, ARCtrl would write the serialisation (harvest) time as `datePublished`.
`SubmissionDate` (`dateCreated`) is never filled from another date.

### 2. Contacts (Creators, Authors, Contributors)

Person and Organization resources linked via `schema:creator`, `schema:author`, or `schema:contributor`. Contacts are
sorted deterministically (family, given, display name, node identity). One contact per person: a Person that matches an
existing contact (same ORCID, else same given and family name, unless both have different ORCIDs) adds its role to that
contact instead of becoming a second one. e!DAL's `author` repeats the creators and the contributors, so its
contributors get the roles author and contributor.

| Schema.org Field         | Description                                                                                                                    | ARC Mapping                                                                                                                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`schema:creator`**     | Authors / creators                                                                                                             | `Investigation.Contacts` (Person with role "author")                                                                                                                                                                 |
| **`schema:author`**      | Authors (alias)                                                                                                                | `Investigation.Contacts` (merged with `creator`, deduped)                                                                                                                                                            |
| **`schema:contributor`** | Contributors                                                                                                                   | `Investigation.Contacts` (role "contributor"; added to an existing contact for the same person)                                                                                                                      |
| **`schema:givenName`**   | Person given name                                                                                                              | `Person.FirstName` (required; mapping error if empty)                                                                                                                                                                |
| **`schema:familyName`**  | Person family name                                                                                                             | `Person.LastName`                                                                                                                                                                                                    |
| **`schema:name`**        | Person display name                                                                                                            | Fallback for name parsing when `givenName`/`familyName` missing                                                                                                                                                      |
| **`schema:affiliation`** | Organization or string                                                                                                         | `Person.Affiliation` (Organization `name`); without it, the first non-empty comma-separated segment of a plain-string `address` (e!DAL writes the institute there)                                                   |
| **`schema:address`**     | Postal address                                                                                                                 | `Person.Address`: a plain string as is (comma/space-only strings are dropped); a PostalAddress as `streetAddress, postalCode, addressLocality, addressRegion, addressCountry`                                        |
| **`schema:email`**       | Email address                                                                                                                  | `Person.Email`                                                                                                                                                                                                       |
| **`schema:url`**         | Person or org URL                                                                                                              | `Person.Comments("URL")`                                                                                                                                                                                             |
| **ORCID**                | Person `@id` or `schema:identifier` (ORCID string/URL; PropertyValue with an orcid.org `value` or a `propertyID` naming ORCID) | `Person.ORCID` (bare iD; RO-Crate Person `@id` `http://orcid.org/<iD>`). One contact per ORCID: a repeated ORCID adds its role. A `creator` without ORCID merged with a same-name `author` keeps the author's ORCID. |
| **Organization nodes**   | `schema:Organization`                                                                                                          | `creator` / `author`: `Investigation.Comment("Creator Organization")` (+ `Creator Organization URL`), one per org; other roles: `Investigation.Comment(role)`; not Person                                            |

### 3. Publications

| Schema.org Field                                | Description                            | ARC Mapping                                                         |
| ----------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------- |
| **DOI from `schema:identifier` or a DOI `@id`** | Canonical DOI (see Identifier Cascade) | `Investigation.Publications` (Publication with DOI, title, authors) |
| **`schema:citation`**                           | Citation text or DOI                   | `Investigation.Publications` (Publication with citation text)       |

### 4. Investigation Comments

| Schema.org Field          | Description                         | ARC Mapping                                                                                                                              |
| ------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **`schema:keywords`**     | Keywords (deduped, sorted casefold) | `Investigation.Comment("Keywords")`                                                                                                      |
| **`schema:license`**      | License identifier or URL           | `ARC.License` (see below) and `Investigation.Comment("License")`                                                                         |
| **`schema:inLanguage`**   | Language code                       | `Investigation.Comment("Language")`                                                                                                      |
| **`schema:version`**      | Dataset version                     | `Investigation.Comment("Version")`                                                                                                       |
| **`schema:url`**          | Landing page URL                    | `Investigation.Comment("URL")`                                                                                                           |
| **`schema:publisher`**    | Publisher (Person or Organization)  | `Investigation.Comment("Publisher")`                                                                                                     |
| **`schema:conformsTo`**   | Specification or standard           | `Investigation.Comment("Conforms To")`                                                                                                   |
| **(title fallback used)** | Which fallback supplied the title   | `Investigation.Comment("Title Source")` — only when `schema:name` did not win; see [Title Resolution Cascade](#title-resolution-cascade) |
| **`schema:distribution`** | `schema:DataDownload` resources     | `Investigation.Comment("Distribution")` (format: `encodingFormat: contentUrl`; several entries semicolon-joined in one Comment)          |

**ARC licence (`ARC.License`).** `schema:license` also sets the ARC licence (`middleware.payload.arc_license`): a
CreativeWork with `url` gives `name (url)`, otherwise the URL or text is used. The licence keeps ARCtrl's `LICENSE` path
(the RO-Crate licence node is `{"@id": "LICENSE", "text": …}`); a URL `@id` would make `ARC.Write` create `https:/…`
directories. Empty values and placeholders (`middleware.payload.placeholders`, e.g. e!DAL's unexpanded `$licenseURL`)
are ignored, for the ARC licence and for the `License`, `Language`, `Version` and `URL` comments; without a licence the
ARCtrl default "ALL RIGHTS RESERVED BY THE AUTHORS" stays.

### 5. Study

| Schema.org Field           | Description        | ARC Mapping                                                                                                             |
| -------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **`schema:name`**          | Dataset title      | `Study.Title` (same resolved title as `Investigation.Title`, see [Title Resolution Cascade](#title-resolution-cascade)) |
| **`schema:description`**   | Abstract / summary | `Study.Description` (fallback: "Imported from Schema.org metadata")                                                     |
| **`schema:datePublished`** | Publication date   | `Study.PublicReleaseDate` (same as the Investigation, see above)                                                        |
| **`schema:dateCreated`**   | Creation date      | `Study.SubmissionDate`                                                                                                  |

### 6. Assay (Measurement)

| Schema.org Field          | Description                     | ARC Mapping                                                                     |
| ------------------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| **`schema:url`**          | Landing page URL                | Assay `Output [URI]` (primary output)                                           |
| **`schema:sameAs`**       | Equivalent URLs                 | Assay `Output [URI]` fallback                                                   |
| **`@id`**                 | Subject IRI                     | Assay `Output [URI]` fallback                                                   |
| **DOI**                   | Canonical DOI                   | Assay `Output [URI]` fallback (`https://doi.org/{doi}`)                         |
| **`schema:distribution`** | `schema:DataDownload` resources | Assay Measurement column `Comment("Distribution")` (entries joined in one cell) |
| **`schema:license`**      | License                         | Assay Measurement column `Comment("License")`                                   |
| **`schema:publisher`**    | Publisher name                  | Assay Measurement column `Comment("Publisher")`                                 |
| **`schema:inLanguage`**   | Language code                   | Assay Measurement column `Comment("Language")`                                  |

## Title Resolution Cascade

The `Investigation`/`Study`/`Assay` title is resolved using the following cascade, stopping at the first non-empty
(trimmed) value:

| Priority | Source                           | Description                                                                                                                                                                                  |
| -------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | **`schema:name`**                | The normal case; no Comment and no warning                                                                                                                                                   |
| 2        | **`schema:headline`**            | Used when `schema:name` is missing or blank                                                                                                                                                  |
| 3        | **`schema:alternativeHeadline`** | First non-empty entry in **casefold-alphabetical order**, the same deterministic ordering used for other multi-value text fields — see the note below on why document order is not available |
| 4        | **HTML page title**              | `html_jsonld`-sourced Datasets only: the fetched page's `citation_title` meta content, else its `<title>` text                                                                               |

**Rules:**

- When step 2, 3, or 4 supplies the title, an `Investigation.Comment("Title Source")` records which fallback won
  (`headline`, `alternativeHeadline`, or `html_title`), and a WARNING is logged. Titles are never silently substituted.
- Mapping **fails closed** when the whole cascade yields nothing — there is no `"Untitled"` default.
- Neither the warning nor any ARC field may contain an rdflib parser-local blank-node label; a subject is identified by
  its IRI when it has one, else by the resolved title.
- Step 4 is computed **lazily** — records whose title resolves at steps 1–3 never pay for the extra HTML parse, and the
  page HTML is fetched only once regardless of call order.
- Step 3 deliberately does **not** use document order. RDF assigns no ordering to repeated predicates — no `@list` is
  involved — so the order in which the source document listed the values does not survive into the graph. Reading raw
  graph objects returns them in rdflib store order, an implementation detail that was observed to differ between running
  the harvester from source and running the shipped PyInstaller binary, which would make the same record map to
  different titles in development and in production. Casefold-alphabetical order is stable everywhere.

Motivating case: OpenAgrar's MyCoRe export omits `schema:name` on a small fraction of otherwise-valid records (see issue
#164).

## Identifier Cascade Precedence

The `Investigation.Identifier` is assigned using the following precedence (highest first). The chosen identifier is
stable across harvests of the same logical dataset:

| Priority | Source                            | Description                                                                                                                                  |
| -------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | **Harvest-source catalog ID**     | `context.harvest_source_id` from discovery (e.g., MyCoRe Solr `id`) — **only when the graph has a single `schema:Dataset`**                  |
| 2        | **Sanitized discovered page URL** | `context.source_url` when no catalog ID; sanitized to identifier-safe slug — **single-Dataset graphs only**                                  |
| 3        | **Canonical HTTP(S) IRI**         | `schema:url` → `schema:sameAs` → subject `@id` (lexicographic minimum, casefold)                                                             |
| 4        | **Canonical DOI**                 | `schema:identifier` (including `schema:PropertyValue` with `propertyID` containing "doi") — only when no higher-precedence identifier exists |

**Multi-Dataset pages:** When a graph contains more than one `schema:Dataset`, steps 1–2 are skipped so each
Investigation uses that Dataset’s own graph URI (step 3) or DOI (step 4). Shared page-level discovery IDs must not
collapse distinct Datasets onto one `Investigation.identifier`.

**Rules:**

- DOIs MUST appear in `Publication` and/or `Investigation` Comments; they MUST NOT become the primary identifier when a
  harvest-source identifier (1 or 2) is available.
- All DOIs are extracted from `schema:identifier` (including `PropertyValue` nodes with `propertyID` containing "doi",
  case-insensitive) and from the Dataset's own `@id` when it is a DOI. A bare-DOI `@id` (e!DAL:
  `"@id": "10.5447/ipk/2011/0"`) is read as `https://doi.org/<doi>` by the JSON-LD parsers; JSON-LD would otherwise
  treat it as a relative IRI and resolve it against the harvester's working directory.
- The canonical DOI is the casefold lexicographic minimum among extracted DOIs.
- Blank-node identifiers are never used (mapping error if no stable identifier found).

## @context handling (parsers)

Remote `@context` / `@import` IRIs are resolved by the shared JSON-LD parsers (`jsonld` / `html_jsonld`) via
[`jsonld-context-loader`](../../openspec/specs/jsonld-context-loader/) and
[`jsonld-parser`](../../openspec/specs/jsonld-parser/) — not by the Schema.org mapper. Remotes are fetched through
`NiceHttpClient` into a process-lifetime cache and inlined before `rdflib` parses, so mapping never triggers uncached
context network I/O.

### Operator pin (`parser.allowed_context_url`)

| Config                                            | Behaviour                                                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Set (one IRI or list)                             | Every payload remote `@context` / `@import` string MUST match an entry after trailing-slash normalisation; an `http` pin also accepts `https` |
| Unset                                             | Remotes are still fetched (legacy); `ParserConfig` warns at load recommending a pin                                                           |
| Relative / non-http(s)                            | Fail closed (`ParserError`)                                                                                                                   |
| HTTP client missing when a remote must be fetched | Fail closed (`ParserError`)                                                                                                                   |

Pin the exact IRI(s) the source emits (e!DAL: `http://schema.org`). There is no code-level Schema.org/Bioschemas
extension allowlist in the mapper; operators extend the pin list in config. See also
[`docs/mappers/README.md`](README.md).

### Context formats

Supported JSON-LD `@context` shapes:

- **String**: `"@context": "https://schema.org/"`
- **List**: `"@context": ["https://schema.org/", {"bios": "https://bioschemas.org/"}]`
- **Dict / inline object**: `"@context": {"schema": "https://schema.org/"}` (inline objects stay allowed without a pin)

## Multi-Dataset Handling

A single page may contain multiple `schema:Dataset` entities (e.g., a DataCatalog with `hasPart` linking to member
Datasets). The mapper handles this as follows:

1. All `schema:Dataset` subjects (in either `http://` or `https://` namespace) are discovered via
   `StableGraph.subjects_of_types` (deduped, sort-key ordered) so multi-Dataset pages yield ARCs in harvest-stable
   order.
2. Each Dataset produces a separate `HarvestedArc` (one Investigation + Study + Assay).
3. `schema:DataCatalog` itself does NOT produce an output — it's a container only.
4. Graphs with no `schema:Dataset` subject raise a mapping error.

## DataDownload Distribution Mapping

Each `schema:DataDownload` linked via `schema:distribution` on the Dataset is mapped to:

1. **Investigation Comment**: `"Distribution"` comment with format `encodingFormat: contentUrl` (or just `contentUrl`
   when `encodingFormat` is absent). Entries without `contentUrl` are skipped.
2. **Assay Measurement column**: The same labels joined into one `"Distribution"` cell (semicolon-separated), so the
   column stays single-row with the other assay fields.

Example:

```json
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "Example Dataset",
  "distribution": [
    {
      "@type": "DataDownload",
      "encodingFormat": "text/csv",
      "contentUrl": "https://repo.example.org/data.csv"
    },
    {
      "@type": "DataDownload",
      "encodingFormat": "application/json",
      "contentUrl": "https://repo.example.org/data.json"
    }
  ]
}
```

Produces two `"Distribution"` comments: `"text/csv: https://repo.example.org/data.csv"` and
`"application/json: https://repo.example.org/data.json"`.
