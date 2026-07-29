# Regal JSON-LD to ARC Mapping Documentation

This document describes how Regal (hbz) JSON-LD research-data records—as returned by
endpoints such as PUBLISSO FRL `/find`—are mapped to the ISA (Investigation, Study, Assay)
model used by ARC.

**Related specs:**

- Harvesting / discovery: [`openspec/specs/regal-jsonld/`](../openspec/specs/regal-jsonld/)
- Implementation contract: [`openspec/specs/regal-to-arc-mapping/`](../openspec/specs/regal-to-arc-mapping/)

> [!NOTE]
> Regal records are **not** schema.org. The JSON-LD `@context` is typically
> `https://frl.publisso.de/context.json` (or an equivalent Regal context). Predicates mix
> Dublin Core Terms, SKOS, BIBO/Bibframe fragments, and the Regal vocabulary
> `http://hbz-nrw.de/regal#`. This document maps **Regal → ARC directly**. The historical
> Publisso→schema.org crosswalk in `m4.2_basic_middleware` (`publisso_conversor.jq`) is a
> conceptual reference for field coverage only.

## Concept

Regal `ResearchData` records describe published research-data packages (results), while ARC
describes the research process. As with INSPIRE and schema.org harvesting, we reconstruct a
minimal ISA workflow that preserves provenance: one Regal record → one Investigation with
one Study and one Assay.

### Scope

| In scope | Out of scope (this mapping) |
| -------- | --------------------------- |
| Records with `contentType: researchData` / `rdftype` `regal:ResearchData` | Articles, monographs, and other Regal content types |
| Bulk `/find` JSON-LD and per-resource `.json` / RDF equivalents | OAI-PMH `oai_dc` (lossy; separate protocol plugin) |
| Core bibliographic, subject, funding, spatial, and file (`hasPart`) fields | Ad-hoc Regal template fields (e.g. livestock/emission facets) unless listed below |

### Protocol-Based Mapping Philosophy

> [!IMPORTANT]
> **Protocols are central to ARC**: They describe how data was created or published.
> Regal metadata rarely encodes laboratory steps; we still model publication as process:
>
> - **Spatial Sampling** — only when recording location / coordinates exist
> - **Data Collection** — subjects, data origin / measurement technique
> - **Data Processing** — repository publication, license, funding context

## Available Regal Metadata Fields

Fields below use the compact JSON keys from Regal `/find` responses. Where useful, the
expanded IRI from the Regal context is noted. Labelled nodes typically expose
`prefLabel` (`skos:prefLabel`) and `@id`.

### 1. Record identity and type

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`@id`** | JSON-LD subject (e.g. `frl:6483993`) | Stable Regal resource id | `Investigation.Identifier` (slug from `@id`); landing URL `https://repository.publisso.de/resource/{@id}` as Assay `Output [URI]` fallback |
| **`doi`** | `regal:doi` | DOI string (without resolver prefix) | `Investigation.Publications` (Publication.DOI); preferred Assay `Output [URI]` as `https://doi.org/{doi}` |
| **`itemID`** | labelled node | OAI identifier (e.g. `oai:frl.publisso.de:frl:…`) | `Investigation` comment `OAI Identifier` |
| **`catalogId`** | — | Catalogue / cataloguing id | `Investigation` comment `Catalog ID` |
| **`rdftype`** | `rdf:type` | Publication type; ResearchData → `http://hbz-nrw.de/regal#ResearchData` | Gate: only map when ResearchData; else mapping error / skip |
| **`contentType`** | `regal:contentType` | Object class (`researchData`, …) | Same gate as `rdftype`; comment `Content Type` when present |
| **`prefLabel`** | `skos:prefLabel` | Display label for the record | Fallback for title if `title` missing |
| **`primaryTopic` / `isPrimaryTopicOf` / `isDescribedBy`** | FRBR/Regal links | Internal graph wiring | **No ARC mapping** (implementation detail) |
| **`transformer`** | — | Available export transformers (`mets`, `mods`, …) | **No ARC mapping** |

### 2. Titles and description

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`title`** | `dcterms:title` (often array) | Main title | `Investigation.Title`, `Study.Title`, `Assay.Title` (first non-empty value) |
| **`alternative`** | `dcterms:alternative` | Alternative / subtitle | `Investigation` comment `Alternative Title` |
| **`description`** | `dcterms:description` (array) | Abstract / summary | `Investigation.Description` and `Study.Description` (join multiple values with a blank line or `;`) |
| **`usageManual`** | `regal:usageManual` | Usage notes | `Study.Description` appendix or `Investigation` comment `Usage Manual` |

### 3. Agents (creators, contributors, institutions)

Labelled agent nodes: `prefLabel` is typically `"FamilyName, Given Name(s)"`; `@id` is often an ORCID URI.

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`creator`** | `dcterms:creator` (`@list`) | Authors | `Investigation.Contacts` (`Person`, role **author**) |
| **`contributor`** | `dcterms:contributor` (`@list`) | Contributors | `Investigation.Contacts` (`Person`, role **contributor**) |
| **`contributorOrder`** | — | Ordered ORCID / agent id pipe-string | Prefer to order Contacts when present; else keep creator/contributor list order |
| **`institution`** | `dbo:institution` | Issuing / collecting organisation (FRL Sammlung) | `Person.Affiliation` on contacts when a single institution applies; else `Investigation` comment `Institution` (`prefLabel` + `@id`) |
| **`lastModifiedBy`** | — | Last editor | `Investigation` comment `Last Modified By` (optional) |

**Person field rules:**

| Person aspect | Source | Rule |
| --- | --- | --- |
| **LastName / FirstName** | `prefLabel` | Split on first `", "`; leftover → FirstName; if no comma, entire label → LastName |
| **ORCID / identifier** | agent `@id` | If ORCID URI, store as Person comment `ORCID` or equivalent identifier field supported by arctrl |
| **Roles** | field provenance | creator → author; contributor → contributor (NCIT role terms when the shared role ontology is used elsewhere in the harvester) |
| **Affiliation** | `institution[].prefLabel` | Apply when exactly one institution, or the same institution is clearly shared |

### 4. Dates, access, and rights

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`issued`** | `dcterms:issued` | Publication / issue year or date | `Investigation.SubmissionDate` / Study submission date when parseable |
| **`yearOfCopyright`** | `regal:yearOfCopyright` | Copyright year | `Investigation` comment `Copyright Year` |
| **`embargoTime`** | — | Embargo end | `Investigation` comment `Embargo` |
| **`accessScheme`** | — | Access scheme | `Investigation` comment `Access Scheme` |
| **`publishScheme`** | — | Publish scheme (`public`, …) | `Investigation` comment `Publish Scheme` |
| **`license`** | `regal:license` (labelled / `@id`) | License URI (preferred) or label | Assay Annotation `Comment [License]`; also Investigation comment `License` |
| **`medium`** | labelled node | Carrier / medium (e.g. Text) | `Investigation` comment `Medium` |

### 5. Subjects, classification, and techniques

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`subject`** | `dcterms:subject` | Subject headings | Ontology-style Investigation comments `keyword [{@id or subject}]` = `prefLabel`, and/or **Data Collection** protocol parameter `Keywords` |
| **`ddc`** | `regal:ddc` | Dewey Decimal class | Same as keywords with TermSourceREF `DDC` / `https://www.oclc.org/en/dewey.html` |
| **`dataOrigin`** | `regal:dataOrigin` | Data origin / Erhebungsform | **Data Collection** protocol parameter `Data Origin` (`prefLabel` + `@id`) |
| **`language`** | `dcterms:language` | Resource language | Assay / Investigation comment `Language` (`prefLabel` or `@id`) |

### 6. Funding

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`fundingId`** | `regal:fundingId` | Funder organisation | **Data Processing** protocol parameter `Funder` (`prefLabel` + `@id`); Investigation comment if multiple |
| **`fundingProgram`** | `regal:fundingProgram` | Funding programme name(s) | **Data Processing** parameter `Funding Program` |
| **`joinedFunding`** | `info:regal/regal/joinedFunding` | Structured grant: programme + funder + project id | **Data Processing** parameters `Funding Program`, `Funder`, `Project ID` from `fundingProgramJoined`, `fundingJoined`, `projectIdJoined` |
| **`projectId`** | — | Project identifier(s) | **Data Processing** parameter `Project ID` when not already taken from `joinedFunding` |

### 7. Files, related works, versions

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`hasPart`** | `dcterms:hasPart` | File / part nodes (`prefLabel`, `@id`) | Assay Annotation comments `Online Resource` / `Online Resource Name` (semicolon-joined); part URL = absolute `@id` when already `http(s)`, else `{resource_base_url}{part @id}` |
| **`associatedPublication`** | URI or node | Related publication | `Investigation.Publications` (title/DOI extracted when possible; else comment with URI) |
| **`associatedDataset`** | — | Related dataset | `Investigation` comment `Associated Dataset` (URI list) |
| **`previousVersion` / `nextVersion`** | — | Version chain | `Investigation` comment `Previous Version` / `Next Version` |
| **`isLike`** | — | Similar / same-as link | `Investigation` comment `Is Like` |
| **`isMemberOf`** | — | Collection membership | `Investigation` comment `Member Of` |
| **`reference`** | — | Bibliographic / external references | `Investigation` comment `Reference` or Publications when DOI-like |

### 8. Spatial coverage

| Regal Field | Context / IRI (typical) | Description | ARC Mapping |
| --- | --- | --- | --- |
| **`recordingCoordinates`** | `regal:recordingCoordinates` | Geo coordinate link (`@id` often a URI) | **Spatial Sampling** protocol parameter `Coordinates` |
| **`recordingLocation`** | `regal:recordingLocation` | Place (`prefLabel`, `@id`) | **Spatial Sampling** protocol parameter `Location` |
| **`recordingPeriod`** | — | Temporal recording period | **Data Collection** protocol parameter `Temporal Extent` |

> [!NOTE]
> Omit the Spatial Sampling protocol entirely when neither `recordingCoordinates` nor
> `recordingLocation` is present (analogous to INSPIRE `nonGeographicDataset`).

### 9. Opaque / repository-specific facets

Fields that appear on some FRL templates (e.g. `emi_measurement_techniques`,
`livestock_category`, `housing_systems`, `emissions`, `ventilation_system`,
`test_design`, `project_title`, `other`, …) are **not** part of the core mapping.

**Rule:** If present, store each as an Investigation comment
`Comment.create(<fieldName>, <stringified value>)` so information is not lost, without
inventing ARC protocol semantics. Promote a facet into a first-class protocol parameter
only after an explicit mapping update to this document.

## Mapping Strategy Summary

### Investigation (Dataset Context)

- **Identifier**: slug from Regal `@id` (required); fail mapping if neither `@id` nor `doi` exists
- **Title**: `title[0]` (fallback `prefLabel`)
- **Description**: joined `description` values
- **SubmissionDate**: `issued` when parseable
- **Contacts**: creators + contributors (ordered)
- **Publications**: DOI publication when `doi` present; plus associated publications when resolvable
- **Comments**: alternative title, license, language, medium, access/publish scheme, copyright year, embargo, OAI/catalog ids, institutions (when not affiliation), version links, opaque facets

### Study (Publication / Processing Workflow)

One Regal ResearchData record = one Study.

- **Identifier**: `[Investigation_ID]_study` (or title slug + `_study`)
- **Title**: same as Investigation title (or `"Study for: " + title`)
- **Description**: description (+ usage manual if present)

**Protocols:**

#### Protocol 1: "Spatial Sampling" (conditional)

- Present only if spatial fields exist
- **Parameters**: Location, Coordinates (as available)
- **Input / Output**: Geographic Region → Selected Location(s) (same pattern as INSPIRE where applicable)

#### Protocol 2: "Data Collection"

- **Parameters**: Keywords / subjects / DDC; Data Origin; Temporal Extent (`recordingPeriod`)
- Omit the protocol only if none of these parameters would be non-empty **and** Spatial Sampling is also omitted—otherwise keep a minimal Data Collection table when subjects or dataOrigin exist

#### Protocol 3: "Data Processing"

- Always present for ResearchData
- **Parameters**: Processing Description (fixed note that metadata comes from Regal/PUBLISSO-style repository); Funder; Funding Program; Project ID; License URI when not only on Assay

### Assay (Data Output)

- **Identifier**: `[Investigation_ID]_assay`
- **MeasurementType**: `Data Collection` (OntologyAnnotation name)
- **TechnologyType**: `Data Repository`
- **TechnologyPlatform**: `Regal Research Data Repository` (or institution `prefLabel` when a single clear platform name is desired)
- **Annotation Table** (exactly one row):
  - **Input [Source Name]**: `"Dataset Source"`
  - **Output [URI]**: `https://doi.org/{doi}` if DOI present → else landing page `https://repository.publisso.de/resource/{@id}` → else raw `@id`
  - **Comment [License]**: license `@id` or label
  - **Comment [Language]**: language prefLabel / `@id`
  - **Comment [Online Resource]**: semicolon-joined `hasPart` URLs
  - **Comment [Online Resource Name]**: semicolon-joined `hasPart` prefLabels (omit column if all empty)
  - **Comment [Institution]**: institution prefLabel(s) when useful on the assay row

### Person (Contacts)

See §3. Prefer ORCID `@id` preservation. Do not invent emails or affiliations Regal does not provide.

### Publications

- Primary: `doi` → `Publication` with Investigation title and author string derived from creator contacts
- Secondary: `associatedPublication` URIs → Publication or Investigation comment with URI

## Special Cases and Limitations

### 1. ResearchData gate

Only records typed as Regal ResearchData (`rdftype` / harvest query `contentType:researchData`) are mapped. Other Regal types must not be forced through this crosswalk.

### 2. Missing identity

If both `@id` and `doi` are absent → mapping error for that record (do not invent identifiers).

### 3. Name splitting

`prefLabel` `"Family, Given"` splitting is best-effort. Unparseable labels keep a single LastName. Do not reverse East-Asian or organisational names heuristically beyond the comma rule.

### 4. Multiple titles / descriptions

Regal often returns arrays. Use the first title for ARC Title fields; join descriptions. Additional titles go to comments.

### 5. License shape

`license` may be an array of labelled nodes. Prefer `@id` (URI). If only `prefLabel` exists, use that string.

### 6. Funding duplication

When both `joinedFunding` and `fundingId` / `fundingProgram` / `projectId` are present, prefer **`joinedFunding`** as the structured source and skip redundant flat fields that duplicate the same funder/programme/project.

### 7. Context resolution

JSON-LD parsing must use the record `@context` (URL or embedded). Mapping operates on the resulting RDF graph (or an equivalent structured model). Do not assume schema.org predicates.

### 8. Relationship to schema.org mapper

`GeneralSchemaOrgMapper` must **not** be reused for Regal graphs. A dedicated Regal mapper implements this document. Field *coverage* may mirror the old Publisso→schema.org jq crosswalk, but the ARC targets above are authoritative.

## Traceability to basic middleware

| Publisso jq → schema.org | Regal source | ARC target (this doc) |
| --- | --- | --- |
| `name` | `title` | Investigation/Study/Assay Title |
| `description` | `description` | Investigation/Study Description |
| `creator` / `contributor` | `creator` / `contributor` | Contacts |
| `sourceOrganization` | `institution` | Affiliation / Institution comment |
| `datePublished` | `issued` | SubmissionDate |
| `identifier` (DOI + frl-internal) | `doi`, `@id` | Publications + Output [URI] |
| `keywords` | `subject`, `ddc` | Keywords / Ontology comments |
| `measurementTechnique` | `dataOrigin` | Data Collection parameter |
| `funder` / `funding` | `fundingId`, `joinedFunding`, … | Data Processing parameters |
| `distribution` | `hasPart` | Assay Online Resource comments |
| `inLanguage` | `language` | Language comment |
| `license` | `license` | License comment |
| `spatial` | `recordingCoordinates`, `recordingLocation` | Spatial Sampling protocol |
