## ADDED Requirements

### Requirement: Title fallback cascade when schema:name is missing

The system SHALL resolve the `Investigation`/`Study`/`Assay` title using the
following cascade, stopping at the first non-empty (trimmed) value:

1. `schema:name`
2. `schema:headline`
3. The first non-empty `schema:alternativeHeadline`, in document order (not
   the alphabetically-sorted order otherwise used for multi-value text
   fields)
4. (`html_jsonld`-sourced Datasets only) An HTML page-title hint: the fetched
   page's `citation_title` meta content, else its `<title>` text

When step 2, 3, or 4 is used, the system MUST append an Investigation
Comment named `"Title Source"` identifying which fallback won, and MUST log
a WARNING-level message. Neither the log message nor any ARC field MAY
contain an rdflib parser-local blank-node label (the subject MUST be
identified by its IRI when it has one, else by the resolved title).

The HTML title hint (step 4) MUST be computed lazily — it MUST NOT be
computed for records whose title already resolved at step 1, 2, or 3.

#### Scenario: schema:name present, no fallback used

- **GIVEN** a `schema:Dataset` with a non-empty `schema:name`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `schema:name`
- **AND** no `"Title Source"` Comment is added and no warning is logged

#### Scenario: headline fallback

- **GIVEN** a `schema:Dataset` with empty/missing `schema:name` and a
  non-empty `schema:headline`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is the `schema:headline` value
- **AND** an Investigation Comment `"Title Source"` = `"headline"` is added
- **AND** a WARNING is logged

#### Scenario: alternativeHeadline fallback uses document order

- **GIVEN** a `schema:Dataset` with no `schema:name`/`schema:headline` and
  `schema:alternativeHeadline` `["Zebra finch population study", "Alpha note
  about metadata"]` in that document order
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `"Zebra finch population study"` (the first
  document-order entry), not `"Alpha note about metadata"` (the
  alphabetically-first entry)

#### Scenario: HTML title hint fallback (html_jsonld sources only)

- **GIVEN** an `html_jsonld`-sourced `schema:Dataset` with no usable
  `schema:name`/`schema:headline`/`schema:alternativeHeadline`, and the
  fetched HTML page has `<meta name="citation_title" content="Citation Title
  From Page">`
- **WHEN** the mapper processes the Dataset
- **THEN** the title is `"Citation Title From Page"`
- **AND** an Investigation Comment `"Title Source"` = `"html_title"` is added

#### Scenario: HTML title hint is not computed when an earlier step resolves

- **GIVEN** an `html_jsonld`-sourced `schema:Dataset` with a non-empty
  `schema:name`
- **WHEN** the mapper processes the Dataset
- **THEN** the HTML title hint is never computed (no second HTML parse pass)

## MODIFIED Requirements

### Requirement: Fail closed on missing required fields

The system SHALL raise a mapping error (not invent fallbacks) when:

- A `schema:Dataset` has no usable title after the full title-fallback
  cascade (see "Title fallback cascade when schema:name is missing")
- A Person contact (creator/author/contributor) would have an empty given
  name
- The identifier cascade yields no usable identifier

#### Scenario: Dataset without any usable title

- **GIVEN** a `schema:Dataset` with no `schema:name`, `schema:headline`, or
  non-empty `schema:alternativeHeadline`, and no HTML title hint available
  (or a non-`html_jsonld` source)
- **WHEN** the mapper processes the Dataset
- **THEN** a mapping error is raised indicating the missing required field
- **AND** no `"Untitled"` placeholder title is invented

#### Scenario: Person contact without given name

- **GIVEN** a `schema:creator` that is a `schema:Person` with only
  `schema:familyName` "Müller"
- **WHEN** the mapper processes the contact
- **THEN** a mapping error is raised indicating the missing given name
