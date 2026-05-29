# EDAL (e!DAL) Schema.org → ARC Mapping

## Scope

Maps e!DAL (Plant Genomics & Phenomics Research Data Repository) schema.org
Dataset JSON-LD to ARC RO-Crate. e!DAL is an IPK Gatersleben repository that
publishes DOIs for plant research datasets. Each DOI landing page embeds a
single `<script type="application/ld+json">` block containing a `schema:Dataset`
with optional Dublin Core conformsTo, Bioschemas profile references, and ORCID
identifiers embedded in author `@id` fields.

## Source Format

The sitemap (XML sitemap protocol) resolves to DOI landing pages that embed
schema.org JSON-LD. A typical dataset JSON-LD looks like:

```json
{
  "@context": "http://schema.org",
  "@type": "Dataset",
  "@id": "10.5447/ipk/2024/0",
  "datePublished": "Thu Feb 15 10:53:48 CET 2024",
  "name": "...",
  "license": "https://creativecommons.org/licenses/by-sa/4.0/legalcode",
  "publisher": { "@type": "Organization", "name": "..." },
  "description": "...",
  "keywords": "Passport data, genebank information, ...",
  "inLanguage": "en",
  "author": [{ "@type": "Person", "givenName": "...", "familyName": "...",
    "@id": "https://orcid.org/0000-0002-3370-3218" }],
  "creator": [{ "@type": "Person", "name": "...", "address": "..." }],
  "contributor": [],
  "http://purl.org/dc/terms/conformsTo": {
    "@type": "CreativeWork",
    "@id": "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"
  }
}
```

## EDAL-Specific Quirks

| Quirk | Source | Handling |
|-------|--------|----------|
| `@id` is a bare DOI (no `https://doi.org/` prefix) | e!DAL generates DOIs as `10.5447/...` and stores only the DOI string | Use as-is for ARC identifier |
| `datePublished` is non-ISO (Java `Date.toString()` format) | e!DAL serialises Java dates as `EEE MMM dd HH:mm:ss zzz yyyy` | Store as-is; no date normalisation |
| ORCID in author `@id` field | e!DAL puts `https://orcid.org/...` in `@id`, also a `PropertyValue` in `identifier` | Extract ORCID from `@id` or `identifier`; store as `Comment("ORCID", orcid)` on Person |
| Flat-string address in `creator` | `address` is sometimes a literal string instead of `PostalAddress` | Accept as flat string on Person |
| Keywords as comma-separated string | e!DAL writes `"Passport data, genebank information"` as a single string, not array | Pass through as-is to Comment |
| `conformsTo` uses DC namespace | Key is `http://purl.org/dc/terms/conformsTo`, not `schema:conformsTo` | Check both DC and schema.org namespaces |
| Empty contributor array | e!DAL includes `"contributor": []` explicitly | Silently skip (no contacts added) |

## Mapping Rules

### ArcInvestigation

| Source | Target | Required | Notes |
|--------|--------|----------|-------|
| `name` | `title` | Y | |
| `description` | `description` | N | Default: `"Imported from e!DAL repository"` |
| `@id` (DOI) | `identifier` | Y | Bare DOI string, no normalisation |
| `datePublished` | `submission_date` | N | Non-ISO format, stored as-is |
| `dateModified` | `submission_date` | N | Fallback if `datePublished` absent |
| `license` | Comment("License") | N | URL string |
| `keywords` | Comment("Keywords") | N | Single comma-separated string, no splitting |
| `inLanguage` | Comment("Language") | N | e.g. "en" |
| `http://purl.org/dc/terms/conformsTo` | Comment("Conforms To") | N | Writes the `@id` value (e.g. Bioschemas profile URL) |
| `schema:conformsTo` | Comment("Conforms To") | N | Fallback if DC namespace not found |
| `distribution` | Comment("Distribution") | N | `encodingFormat: contentUrl` per distribution |
| `citation` | Publication | N | One per citation string |

### Contacts

| Source | Target | Notes |
|--------|--------|-------|
| `author[*]` | Person(role: author) | Includes ORCID extraction |
| `creator[*]` | Person(role: author) | Deduped against existing contacts by name |
| `publisher` | Person(role: publisher) | Organization node → Person with affiliation |
| `contributor[*]` | Person(role: contributor) | |

#### Person Construction

1. Try `givenName` + `familyName` extraction
2. Fall back to splitting `name` on last space → `familyName` is last token
3. Extract ORCID from `@id` (match `orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])`)
4. ORCID stored as `Comment("ORCID", "0000-0002-3370-3218")` on Person
5. Address: if `PostalAddress` node → format `street, postalCode, country`; if literal string → use as-is
6. Empty `givenName` + no `name` → skip contact

### ARC Structure

```
ArcInvestigation (one per e!DAL dataset)
├── Contacts (authors, creators, publisher)
├── Publications (if citation or DOI present)
├── Comments (license, keywords, language, conformsTo, distributions)
└── OntologySourceReferences (SCHEMAORG, NCIT, EDAM)
```

## Excluded Fields

The following e!DAL metadata is not mapped:
- **DC Metadata (`<meta name="DC.*">`)** — Already represented in schema.org JSON-LD
- **File listings** — Not part of schema.org graph; require separate HTML parsing
- **Citation text on landing page** — Available from schema.org citation field instead
- **BibTeX/RIS export links** — Static pages, not part of schema.org payload
