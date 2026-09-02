# Schema.org to ARC Mapping Documentation

This document describes how Schema.org RDF graphs (parsed from JSON-LD embedded in HTML
pages or inline in API responses) are mapped to the ISA (Investigation, Study, Assay)
model used by ARC.

**Related specs:**

- Implementation contract: [`openspec/specs/schemaorg-to-arc-mapping/`](../openspec/specs/schemaorg-to-arc-mapping/)

## Concept

Schema.org metadata describes published datasets, while ARC describes the research
process. We reconstruct a minimal ISA workflow that preserves provenance: one
`schema:Dataset` → one Investigation with one Study and one Assay. A single page
may contain multiple Dataset entities (e.g. DataCatalog with `hasPart`), each
producing a separate Investigation.

### Protocol-Based Mapping Philosophy

> [!IMPORTANT]
> **Protocols are central to ARC**: They describe exactly how data was created. Since
> Schema.org metadata rarely encodes laboratory steps, we model publication as process:
>
> - **Data Collection** — keywords, description, research subject
> - **Data Processing** — repository publication, license, publisher context
> - **Measurement** — dataset landing page URL, distribution file access

### Scope

| In scope | Out of scope |
| --- | --- |
| `schema:Dataset` entities with `@type` in `http://schema.org/` or `https://schema.org/` | Non-Dataset types (`schema:Software`, `schema:Article`, etc.) |
| JSON-LD embedded in HTML or inline API responses | JSON-LD with unknown `@context` (validated before parsing) |
| `schema:DataDownload` distributions | External file downloads not linked via `schema:distribution` |

## Available Schema.org Metadata Fields

Fields below use Schema.org terminology. The mapper supports both `http://schema.org/`
and `https://schema.org/` namespaces (dual-namespace aliasing via `StableGraph`).

### 1. Dataset Identity and Type

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **`@id`** | Subject IRI (blank node or HTTP(S) URI) | `Investigation.Identifier` (when no higher-precedence ID); see [Identifier Cascade](#identifier-cascade-precedence) |
| **`@type`** | Must be `schema:Dataset` | Gate: only Dataset entities are mapped; `DataCatalog` is container, not output |
| **`schema:name`** | Dataset title | `Investigation.Title`, `Study.Title`, `Assay.Title` |
| **`schema:description`** | Abstract / summary | `Investigation.Description`, `Study.Description`, Data Collection parameter |
| **`schema:url`** | Canonical landing page URL | `Investigation.Identifier` (sanitized); Assay `Output [URI]` |
| **`schema:sameAs`** | Equivalent URLs | `Investigation.Identifier` fallback (lexicographic min) |
| **`schema:identifier`** | DOI, URL, or other identifiers | `Investigation.Identifier` (DOI as last resort); Publication DOI; `Investigation.Comment("Alternate Identifier")` |
| **`schema:datePublished`** | Publication date | `Investigation.SubmissionDate`, `Study.SubmissionDate` |
| **`schema:dateModified`** | Last modification date | `Investigation.SubmissionDate` (fallback) |

### 2. Contacts (Creators, Authors, Contributors)

Person and Organization resources linked via `schema:creator`, `schema:author`, or
`schema:contributor`. Contacts are sorted deterministically (family, given, display name,
node identity).

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **`schema:creator`** | Authors / creators | `Investigation.Contacts` (Person with role "author") |
| **`schema:author`** | Authors (alias) | `Investigation.Contacts` (merged with `creator`, deduped) |
| **`schema:contributor`** | Contributors | `Investigation.Contacts` (Person with role "contributor") |
| **`schema:givenName`** | Person given name | `Person.FirstName` (required; mapping error if empty) |
| **`schema:familyName`** | Person family name | `Person.LastName` |
| **`schema:name`** | Person display name | Fallback for name parsing when `givenName`/`familyName` missing |
| **`schema:affiliation`** | Organization or string | `Person.Comments("Affiliation")` |
| **`schema:address`** | Postal address | `Person.Address` |
| **`schema:email`** | Email address | `Person.Email` |
| **`schema:url`** | Person or org URL | `Person.Comments("URL")` |
| **Organization nodes** | `schema:Organization` | `Investigation.Comment(role)` with org name; not Person |

### 3. Publications

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **DOI from `schema:identifier`** | Canonical DOI (see Identifier Cascade) | `Investigation.Publications` (Publication with DOI, title, authors) |
| **`schema:citation`** | Citation text or DOI | `Investigation.Publications` (Publication with citation text) |

### 4. Investigation Comments

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **`schema:keywords`** | Keywords (deduped, sorted casefold) | `Investigation.Comment("Keywords")` |
| **`schema:license`** | License identifier or URL | `Investigation.Comment("License")` |
| **`schema:inLanguage`** | Language code | `Investigation.Comment("Language")` |
| **`schema:version`** | Dataset version | `Investigation.Comment("Version")` |
| **`schema:url`** | Landing page URL | `Investigation.Comment("URL")` |
| **`schema:publisher`** | Publisher (Person or Organization) | `Investigation.Comment("Publisher")` |
| **`schema:conformsTo`** | Specification or standard | `Investigation.Comment("Conforms To")` |
| **`schema:distribution`** | `schema:DataDownload` resources | `Investigation.Comment("Distribution")` (format: `encodingFormat: contentUrl`) |

### 5. Study

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **`schema:name`** | Dataset title | `Study.Title` |
| **`schema:description`** | Abstract / summary | `Study.Description` (fallback: "Imported from Schema.org metadata") |
| **`schema:datePublished`** | Publication date | `Study.SubmissionDate` |

### 6. Assay (Measurement)

| Schema.org Field | Description | ARC Mapping |
| --- | --- | --- |
| **`schema:url`** | Landing page URL | Assay `Output [URI]` (primary output) |
| **`schema:sameAs`** | Equivalent URLs | Assay `Output [URI]` fallback |
| **`@id`** | Subject IRI | Assay `Output [URI]` fallback |
| **DOI** | Canonical DOI | Assay `Output [URI]` fallback (`https://doi.org/{doi}`) |
| **`schema:distribution`** | `schema:DataDownload` resources | Assay Measurement column `Comment("Distribution")` (entries joined in one cell) |
| **`schema:license`** | License | Assay Measurement column `Comment("License")` |
| **`schema:publisher`** | Publisher name | Assay Measurement column `Comment("Publisher")` |
| **`schema:inLanguage`** | Language code | Assay Measurement column `Comment("Language")` |

## Identifier Cascade Precedence

The `Investigation.Identifier` is assigned using the following precedence (highest
first). The chosen identifier is stable across harvests of the same logical dataset:

| Priority | Source | Description |
| --- | --- | --- |
| 1 | **Harvest-source catalog ID** | `context.harvest_source_id` from discovery (e.g., MyCoRe Solr `id`) — **only when the graph has a single `schema:Dataset`** |
| 2 | **Sanitized discovered page URL** | `context.source_url` when no catalog ID; sanitized to identifier-safe slug — **single-Dataset graphs only** |
| 3 | **Canonical HTTP(S) IRI** | `schema:url` → `schema:sameAs` → subject `@id` (lexicographic minimum, casefold) |
| 4 | **Canonical DOI** | `schema:identifier` (including `schema:PropertyValue` with `propertyID` containing "doi") — only when no higher-precedence identifier exists |

**Multi-Dataset pages:** When a graph contains more than one `schema:Dataset`, steps 1–2
are skipped so each Investigation uses that Dataset’s own graph URI (step 3) or DOI
(step 4). Shared page-level discovery IDs must not collapse distinct Datasets onto one
`Investigation.identifier`.

**Rules:**

- DOIs MUST appear in `Publication` and/or `Investigation` Comments; they MUST NOT
  become the primary identifier when a harvest-source identifier (1 or 2) is available.
- All DOIs are extracted from `schema:identifier` (including `PropertyValue` nodes with
  `propertyID` containing "doi", case-insensitive).
- The canonical DOI is the casefold lexicographic minimum among extracted DOIs.
- Blank-node identifiers are never used (mapping error if no stable identifier found).

## @context Validation

Before RDF parsing, the raw JSON-LD payload is validated to ensure the `@context` is
Schema.org or a known extension. This fails closed early (before rdflib parsing) and
rejects unknown vocabularies; HTML extraction already JSON-decodes each block once
for normalization and reuses that object for validation.

### Allowlist

| Context | Status |
| --- | --- |
| `https://schema.org/` | Allowed |
| `http://schema.org/` | Allowed (same vocabulary; dual-namespace aliasing in RDF) |
| `https://schema.org` (no trailing slash) | Allowed |
| `http://schema.org` (no trailing slash) | Allowed |
| `https://bioschemas.org/` | Allowed (known extension) |
| `http://bioschemas.org/` | Allowed (known extension) |
| `https://bioschemas.org` (no trailing slash) | Allowed |
| `http://bioschemas.org` (no trailing slash) | Allowed |
| Any other remote context IRI | **Rejected** (`JsonLdContextError`) |

### Context Formats

The validator supports all JSON-LD `@context` formats:

- **String**: `"@context": "https://schema.org/"`
- **List**: `"@context": ["https://schema.org/", {"bios": "https://bioschemas.org/"}]`
- **Dict**: `"@context": {"schema": "https://schema.org/"}`

Remote context loads via `@import` or a nested `@context` inside a term definition
must be absolute allowlisted `http(s)` IRIs (relative `@import` is rejected).
Absolute `http(s)` `@vocab` values must be allowlisted; relative `@vocab` is
allowed (expansion only). Other JSON-LD keywords (`@language`, `@version`, …)
are ignored.

### Extension Mechanism

New extension contexts can be added by updating `_KNOWN_EXTENSION_CONTEXTS` in
`middleware/linked_data/src/middleware/linked_data/jsonld_validation.py`. The allowlist
is a frozen set — code changes are required to add new extensions.

## Multi-Dataset Handling

A single page may contain multiple `schema:Dataset` entities (e.g., a DataCatalog
with `hasPart` linking to member Datasets). The mapper handles this as follows:

1. All `schema:Dataset` subjects (in either `http://` or `https://` namespace) are
   discovered via `_find_dataset_subjects`.
2. Each Dataset produces a separate `HarvestedArc` (one Investigation + Study + Assay).
3. `schema:DataCatalog` itself does NOT produce an output — it's a container only.
4. Graphs with no `schema:Dataset` subject raise a mapping error.

## DataDownload Distribution Mapping

Each `schema:DataDownload` linked via `schema:distribution` on the Dataset is mapped
to:

1. **Investigation Comment**: `"Distribution"` comment with format `encodingFormat: contentUrl`
   (or just `contentUrl` when `encodingFormat` is absent). Entries without `contentUrl` are skipped.
2. **Assay Measurement column**: The same labels joined into one `"Distribution"`
   cell (semicolon-separated), so the column stays single-row with the other assay fields.

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

Produces two `"Distribution"` comments: `"text/csv: https://repo.example.org/data.csv"`
and `"application/json: https://repo.example.org/data.json"`.
