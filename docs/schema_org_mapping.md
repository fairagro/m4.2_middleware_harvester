# Schema.org to ARC Mapping Documentation

This document describes how Schema.org Dataset metadata is mapped to the ISA (Investigation, Study, Assay) model used by ARC.

## Concept

The goal is to map Schema.org **Dataset** metadata to the ISA model. Schema.org is a collaborative community activity creating a vocabulary of terms that can be used in structured data markup on web pages.

> [!NOTE]
> **Only `@type: "Dataset"` is supported**: This implementation specifically maps Schema.org resources with `"@type": "Dataset"` (or `"type": "Dataset"`) to ARC/ISA structures. Other Schema.org types (e.g., `CreativeWork`, `SoftwareApplication`, `DataCatalog`) are not handled by this mapper.

The Dataset type is commonly used to describe research data publications.

## Available Schema.org Metadata Fields

Schema.org Dataset provides **20+ metadata fields** organized across multiple categories. This section documents all available fields and their ARC mappings.

### 1. Core Dataset Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **@context** | string | JSON-LD context URL (e.g., <https://schema.org>) | Investigation comment (provenance) |
| **@id** | string | Unique identifier (URL or URI) | `Investigation.Identifier` (fallback) |
| **@type** | string/list | RDF type (e.g., "Dataset") | Investigation comment |
| **identifier** | string/dict | Official identifier (DOI, ISBN, etc.) | `Investigation.Identifier` (preferred) / `Publication.DOI` |
| **name** | string | Dataset title | `Investigation.Title` |
| **description** | string | Abstract/summary | `Investigation.Description` |
| **url** | string | Direct URL to dataset | **Assay Annotation Table** `Output [URI]` |
| **inLanguage** | string | Language code (e.g., "en", "de") | **Assay Annotation Table** `Comment [Language]` |
| **version** | string | Version identifier | `Investigation` comment |
| **keywords** | string/list | Descriptive keywords | `Investigation` comment (semicolon-joined) |
| **license** | string/dict | License information | **Assay Annotation Table** `Comment [License]` |

### 2. Date Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **datePublished** | string | Publication date (ISO 8601) | `Investigation.SubmissionDate` |
| **dateModified** | string | Last modification date | `Investigation` comment (fallback for SubmissionDate) |

### 3. Agent Properties (Contacts)

Schema.org supports multiple agent types for contacts.

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **creator** | Person/Organization list | Primary creators | `Investigation.Contacts` with role="author" |
| **author** | Person/Organization list | Authors (alternative to creator) | `Investigation.Contacts` with role="author" |
| **contributor** | Person/Organization list | Contributors | `Investigation.Contacts` with role="contributor" |
| **publisher** | Organization | Publishing organization | **Assay Annotation Table** `Comment [Publisher]` |

### 4. Person Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **givenName** | string | First name | `Person.FirstName` |
| **familyName** | string | Last name | `Person.LastName` |
| **name** | string | Full name (fallback) | Split to `Person.FirstName` / `Person.LastName` |
| **email** | string | Email address | `Person.Email` |
| **url** | string | Personal/professional URL | `Person` comment |
| **address** | PostalAddress/string | Contact address | `Person.Address` (formatted) |

### 5. Organization Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **name** | string | Organization name | `Person.LastName` (organization as contact) |
| **url** | string | Organization website | `Person` comment |
| **address** | PostalAddress/string | Organization address | `Person.Address` |

### 6. PostalAddress Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **streetAddress** | string | Street address | Part of `Person.Address` |
| **postalCode** | string | Postal/ZIP code | Part of `Person.Address` |
| **addressCountry** | string | Country | Part of `Person.Address` |
| **addressLocality** | string | City | Part of `Person.Address` |
| **addressRegion** | string | State/region | Part of `Person.Address` |

### 7. Related Properties

| Schema.org Field | Type | Description | ARC Mapping |
| --- | --- | --- | --- |
| **citation** | string/list | Citations to related works | `Investigation.Publications` |
| **isPartOf** | dict | Parent collection/catalog | `Investigation` comment |
| **includedInDataCatalog** | dict | Data catalog membership | `Investigation` comment |
| **conformsTo** | dict | Conformance specification | `Investigation` comment "Conforms To" |
| **distribution** | list | Distribution/download info | `Investigation` comment (limited to 3) |

## Mapping Strategy Summary

### Investigation (Dataset Context)

- **Identifier**: `identifier` (DOI preferred) → `@id` → slugified `name`
- **Title**: `name`
- **Description**: `description`
- **SubmissionDate**: `datePublished` → `dateModified` (fallback)
- **Contacts**: All `creator`, `author`, `contributor`, and `publisher` mapped to `Person` objects with appropriate roles
- **Publications**: Created from DOI if available (with authors from contacts)
- **Comments/Remarks**:
  - `keywords` (semicolon-joined if list)
  - `license` (if not in assay table)
  - `language`
  - `version`
  - `url`
  - `conformsTo` profile ID
  - `distribution` info (first 3 entries)
  - `isPartOf` and `includedInDataCatalog`

### Ontology Sources

The following ontology sources are automatically added to the Investigation:

| Name | URL | Description |
| --- | --- | --- |
| **SCHEMAORG** | <https://schema.org/> | Schema.org vocabulary for structured data |
| **NCIT** | <http://purl.obolibrary.org/obo/ncit.owl> | NCI Thesaurus |
| **EDAM** | <http://edamontology.org> | EDAM Bioinformatics Ontology |

### Study (Research Unit / Data Processing Workflow)

One Schema.org Dataset = One Study representing the data lifecycle.

- **Identifier**: `[investigation_slug]_study`
- **Title**: "Study for: " + [Investigation Title]
- **Description**: "Imported from Schema.org metadata"

**Process-Oriented Protocols**:

#### Protocol 1: "Data Collection" (conditional)

Created only if `keywords` or `description` are available.

- **Input**: "Research Subject"
- **Parameters**: `Keywords` (as ontology term)
- **Output**: Empty (intermediate)

#### Protocol 2: "Data Processing" (always created)

- **Input**: "Raw Data" (using `CompositeCell.create_data_from_string`)
- **Parameters**: "Processing Description" with standard text + publisher info
- **Output**: "Published Dataset" (using `CompositeCell.create_data_from_string`)

### Assay (Measurement / Data Output)

- **Identifier**: `[investigation_slug]_assay`
- **Title**: Same as Investigation Title
- **MeasurementType**: `OntologyAnnotation(name="Data Collection")`
- **TechnologyType**: `OntologyAnnotation(name="Data Repository")`
- **TechnologyPlatform**: `OntologyAnnotation(name="Schema.org Data Repository")`
- **Annotation Table** (always exactly one row):
  - **Input [Source Name]**: `"Dataset Source"`
  - **Output [URI]**: `url` → `@id` → `[slug]_dataset` (fallback)
  - **Comment [License]**: `license` (present only if available)
  - **Comment [Publisher]**: `publisher.name` (present only if available)
  - **Comment [Language]**: `inLanguage` (present only if available)

### Person (Contacts)

Map all `creator`, `author`, `contributor`, and `publisher` agents:

- **FirstName / LastName**: From `givenName` / `familyName`, or split from `name`
- **Email**: `email`
- **Address**: Formatted from `PostalAddress` components or raw string
- **Affiliation**: `organisationName` (for organizations)
- **Roles**:
  - `creator`/`author` → `OntologyAnnotation(name="author")`
  - `contributor` → `OntologyAnnotation(name="contributor")`
  - `publisher` → `OntologyAnnotation(name="publisher")`
- **Comments**: `url` (personal/professional website)

### Publication (DOI-based)

If a DOI is extractable from `identifier` or `@id`:

- **Title**: Dataset `name`
- **Authors**: Formatted from contacts with "author" role
- **DOI**: Extracted DOI

## Identifier and DOI Extraction

The mapper uses a priority-based approach for identifiers:

1. **DOI from `identifier`**: If `identifier` starts with "10.", it's used directly
2. **DOI from `@id`**: Extract DOI from URLs like `https://doi.org/10.xxxx/...`
3. **Raw `@id`**: Use as fallback identifier
4. **Slugified name**: Generate machine-readable slug from title

DOI extraction pattern: `10.\d{4,9}/[-._;()/:A-Z0-9]+`

## Special Cases and Limitations

### 1. Duplicate Author Handling

When both `creator` and `author` are present, the mapper checks for duplicates by comparing first and last names. Duplicate authors are skipped to avoid redundant contacts.

### 2. Organization vs Person

Organizations are mapped as `Person` objects with:

- `LastName` = organization name
- `FirstName` = empty string
- `Affiliation` = organization name

### 3. Address Handling

Addresses can be either:

- **String**: Used directly as `Person.Address`
- **PostalAddress object**: Formatted as "street, postalCode, country"

### 4. License Handling

License information appears in two places:

- **Investigation comment**: For metadata-level documentation
- **Assay table column**: For data-level licensing (preferred)

### 5. Distribution Information

Distribution entries are limited to the first 3 to avoid excessive comments. Each is formatted as "encodingFormat: contentUrl".

## Repo-Specific Mappings

### BONARES

- **Identifier**: Extracted from DOI pattern in identifier field
- **Creators**: Mapped from `author[].contactPoint` with:
  - `FirstName`, `LastName`: Split from `contactPoint.name`
  - `Email`: `contactPoint.email`
  - `Phone`: `contactPoint.telephone`
  - `Role`: `contactPoint.contactType`
  - `Affiliation`: Author organization name

### EDAL

- **Identifier**: Direct `@id` field
- **Creators**: Mapped from `creator[]` with:
  - `FirstName`: `creator.givenName`
  - `LastName`: `creator.familyName`
  - `Address`: Formatted from `creator.address` (dict or string)
- **Publications**: Automatically created with DOI as identifier

### OpenAgrar

- **Identifier**: Extracted from `identifier[]` array where `propertyID == "doi"`
- **Description**: `headline` field (fallback: "No description available")
- **Title**: `name` field (fallback: "No title available")
- **Creators**: Mapped from `creator[]` with:
  - `FirstName`: `creator.givenName`
  - `LastName`: `creator.familyName`
  - `Affiliation`: `creator.affiliation`
- **Publisher-based Routing**:
  - If "Thünen" in publisher name → `thunen_atlas` repository
  - Otherwise → `openagrar` repository
