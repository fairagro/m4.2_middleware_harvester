# Schema.org to ARC Mapping - Design

## Mapping Overview

The Schema.org to ARC mapper converts Schema.org Dataset metadata into the ARC (Annotated Research Context) structure used by FAIRagro. The mapping follows the same pattern as the INSPIRE mapper but is adapted for Schema.org's JSON-LD structure.

## Field Mapping Table

### Investigation Level

| Schema.org Field | ARC Field | Notes |
|-----------------|-----------|-------|
| `@id` or `identifier` | `Investigation.Identifier` | DOI extracted if present |
| `name` | `Investigation.Title` | |
| `description` | `Investigation.Description` | |
| `datePublished` | `Investigation.SubmissionDate` | Falls back to `dateModified` |
| `creator` | `Investigation.Contacts` | With "author" role |
| `author` | `Investigation.Contacts` | With "author" role |
| `contributor` | `Investigation.Contacts` | With "contributor" role |
| `publisher` | `Investigation.Contacts` | With "publisher" role |
| `keywords` | `Investigation.Comments` | As "Keywords" comment |
| `license` | `Investigation.Comments` | As "License" comment |
| `inLanguage` | `Investigation.Comments` | As "Language" comment |
| `version` | `Investigation.Comments` | As "Version" comment |
| `url` | `Investigation.Comments` | As "URL" comment |
| `distribution` | `Investigation.Comments` | First 3 distributions |
| `conformsTo` | `Investigation.Comments` | Profile information |
| `citation` | `Investigation.Publications` | Additional publications |

### Person Mapping

| Schema.org Field | ARC Person Field | Notes |
|-----------------|-----------------|-------|
| `givenName` | `FirstName` | |
| `familyName` | `LastName` | |
| `name` | Split into First/Last | If givenName/familyName missing |
| `email` | `Email` | |
| `url` | `Comments` | As "URL" comment |
| `address` | `Address` | Formatted from PostalAddress or string |

### Study Level

The Study contains process-oriented protocols:

1. **Data Collection Protocol** (if keywords/description available)
   - Input: Research Subject
   - Parameter: Keywords
   - Output: Collected Data

2. **Data Processing Protocol** (always created)
   - Input: Raw Data
   - Parameter: Processing Description (includes publisher info)
   - Output: Published Dataset

### Assay Level

The Assay contains a measurement annotation table:

| Column Type | Content |
|------------|---------|
| Input [Source] | "Dataset Source" |
| Output [URI] | Dataset URL or identifier |
| Comment [License] | License information (if present) |
| Comment [Publisher] | Publisher name (if present) |
| Comment [Language] | Language (if present) |

## Ontology Sources

The following ontology sources are registered:
- **SCHEMAORG**: Schema.org vocabulary (https://schema.org/)
- **NCIT**: NCI Thesaurus
- **EDAM**: Bioinformatics Ontology

## Identifier Handling

DOIs are extracted from:
1. `@id` field if it contains "doi.org" or starts with "10."
2. `identifier` field if it starts with "10."

If no DOI is found, the identifier is slugified from the title for filesystem compatibility.

## Special Cases

### Duplicate Authors
When both `creator` and `author` fields are present, duplicates are detected by comparing first/last names and only added once.

### Organization as Contact
Organizations are mapped as Person objects with the organization name as the last name and affiliation.

### Address Formatting
PostalAddress objects are formatted as comma-separated strings. String addresses are used directly.