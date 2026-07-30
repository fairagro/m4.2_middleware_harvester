# XML Sitemap Parser

## Purpose

Parse standard XML sitemap documents and yield discovery results for Linked
Data harvesting. The parser does not fetch dataset payloads or perform ARC
mapping.

## Requirements

### Requirement: SitemapType.xml configuration

The system SHALL support `SitemapType.xml` in linked-data plugin configuration
and accept a single sitemap entry-point URL.

#### Scenario: XML sitemap type is selectable

- **WHEN** plugin config sets `sitemap_type: xml` with a `sitemap_url`
- **THEN** the plugin uses the XML sitemap implementation for discovery

### Requirement: Sitemap protocol parsing

The system SHALL parse XML sitemap documents according to the sitemap protocol
and support both `urlset` and `sitemapindex` document roots.

#### Scenario: urlset and sitemapindex

- **WHEN** the entry document is a `urlset` or a `sitemapindex`
- **THEN** the parser processes that root type without requiring a different
  config switch

### Requirement: Nested indexes and loop prevention

The system SHALL recursively follow nested `sitemapindex` entries and MUST
track already-visited sitemap URLs so cycles are skipped silently.

#### Scenario: Already-visited sitemap URL

- **WHEN** a nested index points at a sitemap URL already visited in this run
- **THEN** that sitemap is skipped and discovery continues

### Requirement: Dataset URL discovery and deduplication

The system SHALL yield one `UrlDiscoveryResult` per unique dataset URL found in
a `urlset`. Duplicate dataset URLs already yielded in the current run MUST be
signalled as `SkippedRecord` (not as failures).

#### Scenario: Duplicate dataset URL

- **WHEN** the same dataset URL appears again in this harvest run
- **THEN** the duplicate is yielded/counted as `SkippedRecord`

### Requirement: Empty loc elements

The system SHALL yield `RecordProcessingError` for missing or empty `<loc>`
elements in both `urlset` and `sitemapindex` documents and MUST NOT silently
skip them. Discovery of remaining entries continues.

#### Scenario: Blank loc in urlset

- **WHEN** a `<url>` entry has an empty `<loc>`
- **THEN** a `RecordProcessingError` is yielded and remaining URLs are still
  processed

### Requirement: Safe XML parsing

The system SHALL parse untrusted sitemap XML with `defusedxml`.

#### Scenario: External sitemap body

- **WHEN** sitemap content is fetched from a remote URL
- **THEN** parsing uses `defusedxml` rather than the stdlib XML parser alone

### Requirement: Fatal parse failures

The system SHALL fail fast with `LinkedDataSitemapError` when XML parsing fails
(malformed or non-XML body) or when the document root is unsupported. That
fatal discovery error is surfaced into the harvest report by the plugin
producer.

#### Scenario: Malformed XML body

- **WHEN** the sitemap response body cannot be parsed as XML
- **THEN** `LinkedDataSitemapError` is raised for that discovery failure

#### Scenario: Unsupported root element

- **WHEN** the root element is neither `urlset` nor `sitemapindex`
- **THEN** `LinkedDataSitemapError` is raised

### Requirement: Edge case — empty urlset

When a `urlset` contains no usable dataset URLs, discovery MUST yield zero
`UrlDiscoveryResult` values and exit cleanly.

#### Scenario: Empty urlset

- **WHEN** the sitemap is a valid empty `urlset`
- **THEN** no dataset discovery results are yielded and discovery completes
  without error
