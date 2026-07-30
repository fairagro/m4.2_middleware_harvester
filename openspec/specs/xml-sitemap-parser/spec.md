# XML Sitemap Parser

## Purpose

Parse standard XML sitemap documents and yield discovery results for Schema.org harvesting.

## Requirements

### Requirement: Support SitemapType.xml in plugin configuration
The system SHALL support `SitemapType.xml` in plugin configuration.

#### Scenario: Satisfies — Support SitemapType.xml in plugin configuration
- **WHEN** the conditions described by this requirement apply
- **THEN** Support `SitemapType.xml` in plugin configuration

### Requirement: Accept a single sitemap entry point URL in plugin configuration
The system SHALL accept a single sitemap entry point URL in plugin configuration.

#### Scenario: Satisfies — Accept a single sitemap entry point URL in plugin configuration
- **WHEN** the conditions described by this requirement apply
- **THEN** Accept a single sitemap entry point URL in plugin configuration

### Requirement: Parse XML sitemap documents according to the sitemap protocol
The system SHALL parse XML sitemap documents according to the sitemap protocol.

#### Scenario: Satisfies — Parse XML sitemap documents according to the sitemap protocol
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse XML sitemap documents according to the sitemap protocol

### Requirement: Support both urlset and sitemapindex document roots
The system SHALL support both `urlset` and `sitemapindex` document roots.

#### Scenario: Satisfies — Support both urlset and sitemapindex document roots
- **WHEN** the conditions described by this requirement apply
- **THEN** Support both `urlset` and `sitemapindex` document roots

### Requirement: Recursively follow nested sitemap indexes
The system SHALL recursively follow nested sitemap indexes.

#### Scenario: Satisfies — Recursively follow nested sitemap indexes
- **WHEN** the conditions described by this requirement apply
- **THEN** Recursively follow nested sitemap indexes

### Requirement: Prevent sitemap loops by tracking already visited sitemap URLs
The system SHALL prevent sitemap loops by tracking already visited sitemap URLs.

#### Scenario: Satisfies — Prevent sitemap loops by tracking already visited sitemap URLs
- **WHEN** the conditions described by this requirement apply
- **THEN** Prevent sitemap loops by tracking already visited sitemap URLs

### Requirement: Deduplicate discovered dataset URLs before yielding results (as SkippedRecord)
The system SHALL deduplicate discovered dataset URLs before yielding results (as `SkippedRecord`).

#### Scenario: Satisfies — Deduplicate discovered dataset URLs before yielding results (as SkippedRecord)
- **WHEN** the conditions described by this requirement apply
- **THEN** Deduplicate discovered dataset URLs before yielding results (as `SkippedRecord`)

### Requirement: Yield RecordProcessingError for empty <loc> elements (do not silently skip)
The system SHALL yield `RecordProcessingError` for empty `<loc>` elements (do not silently skip).

#### Scenario: Satisfies — Yield RecordProcessingError for empty <loc> elements (do not silently skip)
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield `RecordProcessingError` for empty `<loc>` elements (do not silently skip)

### Requirement: Yield one UrlDiscoveryResult per unique dataset URL found in a…
The system SHALL yield one `UrlDiscoveryResult` per unique dataset URL found in a `urlset`.

#### Scenario: Satisfies — Yield one UrlDiscoveryResult per unique dataset URL found in a…
- **WHEN** the conditions described by this requirement apply
- **THEN** Yield one `UrlDiscoveryResult` per unique dataset URL found in a `urlset`

### Requirement: Use safe XML parsing (defusedxml) for untrusted content
The system SHALL use safe XML parsing (`defusedxml`) for untrusted content.

#### Scenario: Satisfies — Use safe XML parsing (defusedxml) for untrusted content
- **WHEN** the conditions described by this requirement apply
- **THEN** Use safe XML parsing (`defusedxml`) for untrusted content

### Requirement: Fail fast with LinkedDataSitemapError when XML parsing fails (malformed
The system SHALL fail fast with `LinkedDataSitemapError` when XML parsing fails (malformed.

#### Scenario: Satisfies — Fail fast with LinkedDataSitemapError when XML parsing fails (malformed
- **WHEN** the conditions described by this requirement apply
- **THEN** Fail fast with `LinkedDataSitemapError` when XML parsing fails (malformed

### Requirement: Edge case — - Duplicate dataset URLs across nested sitemaps
The system SHALL handle this edge case: when - Duplicate dataset URLs across nested sitemaps, then yield only the first occurrence. - A sitemap URL already visited in the current traversal → skip silently. - Missing or empty `<loc>` elements → yield `RecordProcessingError` without stopping discovery. - Duplicate dataset URL already yielded in this run → `SkippedRecord`. - Empty `urlset` → yield zero results and exit cleanly. - Malformed / non-XML body → raise `LinkedDataSitemapError` (fatal discovery failure; plugin producer yields it into the harvest report). - Unsupported root element → raise `LinkedDataSitemapError` the same way.

#### Scenario: Edge case — - Duplicate dataset URLs across nested sitemaps
- **WHEN** - Duplicate dataset URLs across nested sitemaps
- **THEN** yield only the first occurrence. - A sitemap URL already visited in the current traversal → skip silently. - Missing or empty `<loc>` elements → yield `RecordProcessingError` without stopping discovery. - Duplicate dataset URL already yielded in this run → `SkippedRecord`. - Empty `urlset` → yield zero results and exit cleanly. - Malformed / non-XML body → raise `LinkedDataSitemapError` (fatal discovery failure; plugin producer yields it into the harvest report). - Unsupported root element → raise `LinkedDataSitemapError` the same way
