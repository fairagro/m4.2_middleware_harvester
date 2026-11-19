# Spec Delta

## MODIFIED Requirements

### Requirement: Title fallback cascade when schema:name is missing

The system SHALL resolve the `Investigation`/`Study`/`Assay` title using the following cascade, stopping at the first
non-empty (trimmed) value:

1. `schema:name`
2. `schema:headline`
3. The first non-empty `schema:alternativeHeadline` in casefold-alphabetical order — the same deterministic ordering
   used for other multi-value text fields. Document order MUST NOT be relied on: RDF assigns no order to repeated
   predicates (no `@list` is involved), so the order in which the source document listed the values does not survive
   into the graph. Reading raw graph objects yields rdflib store order, which is an implementation detail and has been
   observed to differ between running from source and running the shipped PyInstaller binary; the same record would then
   map to different titles in development and in production.
4. (`html_jsonld`-sourced Datasets only) An HTML page-title hint: the fetched page's `citation_title` meta content, else
   its `<title>` text

When step 2, 3, or 4 is used, the system MUST append an Investigation Comment named `"Title Source"` identifying which
fallback won, MUST log a WARNING-level message, and MUST attach a corresponding dataset warning message on the yielded
`HarvestedArc`. Neither the log message, the report warning message, nor any ARC field MAY contain an rdflib
parser-local blank-node label (the subject MUST be identified by its IRI when it has one, else by the resolved title).

The HTML title hint (step 4) MUST be computed lazily — it MUST NOT be computed for records whose title already resolved
at step 1, 2, or 3.

#### Scenario: schema:name present, no fallback used

- **GIVEN** a `schema:Dataset` with a non-empty `schema:name`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `schema:name`
- **AND** no `"Title Source"` Comment is added, no warning is logged, and the yielded `HarvestedArc` carries no
  title-fallback warning

#### Scenario: headline fallback

- **GIVEN** a `schema:Dataset` with empty/missing `schema:name` and a non-empty `schema:headline`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is the `schema:headline` value
- **AND** an Investigation Comment `"Title Source"` = `"headline"` is added
- **AND** a WARNING is logged
- **AND** the yielded `HarvestedArc` carries a dataset warning describing the title fallback

#### Scenario: alternativeHeadline fallback is order-stable across environments

- **GIVEN** a `schema:Dataset` with no `schema:name`/`schema:headline` and `schema:alternativeHeadline`
  `["Zebra finch population study", "Alpha note about metadata"]` in that document order
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `"Alpha note about metadata"` (the casefold-alphabetically first entry), not
  `"Zebra finch population study"` (the document-first entry)
- **AND** the same value is chosen whether the harvester runs from source or as the packaged binary
- **AND** the yielded `HarvestedArc` carries a dataset warning describing the title fallback

#### Scenario: HTML title hint fallback (html_jsonld sources only)

- **GIVEN** an `html_jsonld`-sourced `schema:Dataset` with no usable
  `schema:name`/`schema:headline`/`schema:alternativeHeadline`, and the fetched HTML page has
  `<meta name="citation_title" content="Citation Title From Page">`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `"Citation Title From Page"`
- **AND** an Investigation Comment `"Title Source"` = `"html_title"` is added
- **AND** the yielded `HarvestedArc` carries a dataset warning describing the title fallback

#### Scenario: HTML title hint is not computed when an earlier step resolves

- **GIVEN** an `html_jsonld`-sourced `schema:Dataset` with a non-empty `schema:name`
- **WHEN** the mapper processes the Dataset
- **THEN** the HTML title hint is never computed (no second HTML parse pass)

### Requirement: Dates MUST be ISO 8601

`GeneralSchemaOrgMapper` MUST pass `datePublished`, `dateModified` and `dateCreated` through
`middleware.payload.iso_dates.iso_date` before writing them to an Investigation or Study date. ISO 8601 dates and
date-times MUST pass unchanged. Java `Date.toString()` values with an unambiguous zone abbreviation MUST become an ISO
date-time with that zone's offset, keeping the local day, MUST log a warning, and MUST attach a corresponding dataset
warning on the yielded `HarvestedArc`. Other values MUST NOT be written as a date: they MUST log a warning, be kept as
the Investigation Comment `Unparsed <term>`, and MUST attach a corresponding dataset warning on the yielded
`HarvestedArc`. Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`) is the first of `datePublished`,
`dateModified`, `dateCreated` that is a date. `SubmissionDate` (RO-Crate `dateCreated`) is `dateCreated` only.

#### Scenario: e!DAL Java date

- **WHEN** `datePublished` is `Sat Jan 01 00:00:00 CET 2011`
- **THEN** Investigation and Study `PublicReleaseDate` MUST be `2011-01-01T00:00:00+01:00`, `SubmissionDate` MUST be
  empty and the RO-Crate root MUST NOT have `dateCreated` (not even an empty string)
- **AND** the yielded `HarvestedArc` carries a dataset warning about the date normalisation

#### Scenario: ISO year

- **WHEN** `datePublished` is `2011`
- **THEN** `PublicReleaseDate` MUST be `2011` and no warning is logged
- **AND** the yielded `HarvestedArc` carries no date warning for that term

#### Scenario: Not a date

- **WHEN** `datePublished` is `sometime in 2011` and there is no other date
- **THEN** `PublicReleaseDate` MUST be empty and the Comment `Unparsed datePublished` MUST hold `sometime in 2011`
- **AND** the yielded `HarvestedArc` carries a dataset warning about the unparsed date

#### Scenario: Creation and publication dates

- **WHEN** `datePublished` is `2011-01-01` and `dateCreated` is `2010-06-30`
- **THEN** the RO-Crate root `datePublished` MUST be `2011-01-01` and `dateCreated` MUST be `2010-06-30`, also after the
  API reads the RO-Crate and writes it with `ARC.Write`

#### Scenario: No publication date

- **WHEN** there is no `datePublished`, `dateModified` is `2014` and `dateCreated` is `2010`
- **THEN** `PublicReleaseDate` MUST be `2014`
