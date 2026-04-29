# Schema.org Harvesting

## Overview

This document describes the architecture for harvesting Schema.org metadata from research data repositories (RDIs). The harvesting system supports multiple source types and extraction methods:

1. **Direct JSON-LD sources** - Pre-aggregated JSON files containing Schema.org Dataset objects
2. **Sitemap-based harvesting** - XML or JSON sitemaps that list dataset URLs
3. **Embedded JSON-LD extraction** - HTML pages with embedded `<script type="application/ld+json">` metadata

## Requirements

### Core Requirements

- [ ] Support fetching Schema.org JSON data from multiple source types:
  - [ ] HTTP/HTTPS URLs (API endpoints, JSON files)
  - [ ] Local file paths
  - [ ] Directory paths (merge multiple JSON files)
- [ ] Parse JSON-LD context and extract Schema.org Dataset objects
- [ ] Handle batch processing of multiple datasets from a single source
- [ ] Support provider-specific filtering via `source_identifier` configuration
- [ ] Implement timeout configuration for HTTP requests
- [ ] Handle JSON parsing errors gracefully with appropriate error reporting

### Sitemap Parsing Requirements (m4.2_basic_middleware)

- [ ] Support XML sitemaps (sitemaps.org standard)
- [ ] Support JSON sitemaps (repository-specific formats)
- [ ] Support text-based sitemaps
- [ ] Extract dataset URLs from sitemap entries
- [ ] Handle sitemap pagination/index sitemaps

### Embedded JSON-LD Extraction Requirements (m4.2_basic_middleware)

- [ ] Fetch HTML pages from dataset URLs
- [ ] Extract `<script type="application/ld+json">` elements
- [ ] Parse embedded JSON-LD using `extruct` library
- [ ] Handle multiple JSON-LD blocks per page
- [ ] Filter for `@type: "Dataset"` entries
- [ ] Log parsing errors without failing entire harvest

## Architecture

### Component Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                    MetadataScraper (Orchestrator)                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  SitemapParser   │  │ MetadataExtractor│  │ HttpSession  │  │
│  │  (Abstract)      │  │ (Abstract)       │  │              │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘  │
│           │                     │                                │
│  ┌────────┼─────────┐  ┌───────┼──────────┐                     │
│  │        │         │  │       │          │                     │
│  ▼        ▼         ▼  ▼       ▼          ▼                     │
│  XML   JSON    Text  Emb.JSON  Raw        HTTP                  │
│  Parser Parser Parser LD       Metadata   Client                │
└─────────────────────────────────────────────────────────────────┘
```

### SitemapParser Hierarchy (m4.2_basic_middleware)

```text
SitemapParser (Abstract Base Class)
├── SitemapParserXml (XML sitemaps, sitemaps.org)
├── SitemapParserJson (JSON sitemaps)
├── SitemapParserText (Text-based sitemaps)
├── SitemapParserOpenAgrar (OpenAgrar JSON format)
├── SitemapParserPublisso (Publisso format)
└── SitemapParserThunenAtlas (Thünen Atlas format)
```

### MetadataExtractor Hierarchy (m4.2_basic_middleware)

```text
MetadataExtractor (Abstract Base Class)
├── MetadataExtractorEmbeddedJsonld (HTML with embedded JSON-LD)
└── MetadataExtractorJsonld (Direct JSON-LD parsing)
```

## Configuration

### Plugin Configuration (this repository)

The plugin uses the following configuration parameters:

| Parameter | Type | Required | Default | Description |
| --------- | ---- | -------- | ------- | ----------- |
| `json_source_url` | string | Yes | - | URL or path to the Schema.org JSON source |
| `json_source_type` | string | No | "url" | Type of source: "url", "file", or "directory" |
| `source_identifier` | string | No | null | Optional identifier to filter sources |
| `timeout` | int | No | 30 | Request timeout in seconds |
| `batch_size` | int | No | 50 | Number of records to process per batch |

### Sitemap-Based Configuration (m4.2_basic_middleware)

For full sitemap-based harvesting, the following configuration is used:

```yaml
sitemaps:
  - name: "openagrar"
    url: "https://www.openagrar.de/sitemap.json"
    sitemap: "openagrar"  # Parser identifier
    metadata: "embedded_jsonld"  # Extractor identifier
    http_client:
      timeout: 30
      headers:
        User-Agent: "FAIRagro Middleware Harvester"
```

## Source Types

### URL Source

Fetches JSON from an HTTP/HTTPS endpoint:

```yaml
schema_org:
  json_source_url: "https://example.com/datasets.json"
  json_source_type: "url"
  timeout: 60
```

### File Source

Reads JSON from a local file:

```yaml
schema_org:
  json_source_url: "/path/to/datasets.json"
  json_source_type: "file"
```

### Directory Source

Reads and merges all JSON files in a directory:

```yaml
schema_org:
  json_source_url: "/path/to/json/files/"
  json_source_type: "directory"
```

## Sitemap Formats

### XML Sitemap (sitemaps.org)

Standard XML format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.org/dataset/1</loc>
    <lastmod>2024-01-01</lastmod>
  </url>
  <url>
    <loc>https://example.org/dataset/2</loc>
    <lastmod>2024-01-02</lastmod>
  </url>
</urlset>
```

### JSON Sitemap (OpenAgrar)

Repository-specific JSON format:

```json
{
  "response": {
    "docs": [
      {"id": "12345"},
      {"id": "67890"}
    ]
  }
}
```

Parsed to URLs: `https://www.openagrar.de/receive/12345`

### Text Sitemap

Simple newline-separated URLs:

```text
https://example.org/dataset/1
https://example.org/dataset/2
```

## Embedded JSON-LD Extraction

### HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
  <title>Dataset Page</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Example Dataset",
    "description": "..."
  }
  </script>
</head>
<body>...</body>
</html>
```

### Extraction Process

1. **Fetch HTML** - Download page content via HTTP
2. **Parse HTML** - Use BeautifulSoup to find `<script type="application/ld+json">` elements
3. **Extract JSON-LD** - Use `extruct` library with `syntaxes=['json-ld']`
4. **Filter Datasets** - Keep only entries with `@type: "Dataset"`
5. **Error Handling** - Log parsing errors, skip invalid entries

### Extraction Code Pattern

```python
from extruct import extract
from bs4 import BeautifulSoup

def extract_embedded_jsonld(html_content: str, url: str) -> list[dict]:
    """Extract embedded JSON-LD from HTML."""
    metadata = extract(
        html_content,
        base_url=url,
        uniform=True,
        syntaxes=['json-ld']
    )
    return metadata.get('json-ld', [])
```

## Harvesting Workflow

### Direct JSON Source (this repository)

```text
1. Fetch JSON from URL/file/directory
2. Parse as list of SchemaOrgDataset objects
3. Map each dataset to ARC
4. Yield RO-Crate JSON
```

### Sitemap-Based Harvesting (m4.2_basic_middleware)

```text
1. Fetch sitemap (XML/JSON/Text)
2. Parse sitemap to extract dataset URLs
3. For each URL:
   a. Fetch HTML content
   b. Extract embedded JSON-LD
   c. Filter for @type: "Dataset"
4. Map each dataset to ARC (this repository)
5. Yield RO-Crate JSON
```

## Error Handling

### Sitemap Parsing Errors

- Log error with sitemap URL
- Skip entire repository if sitemap cannot be parsed
- Report: `{'valid_entries': 0, 'failed_entries': 1, 'skipped': True}`

### Dataset Extraction Errors

- Log error with dataset URL
- Skip individual dataset
- Continue with remaining URLs
- Report: `{'valid_entries': N, 'failed_entries': M, 'skipped': False}`

### JSON-LD Parsing Errors

- Log error with suspicious data
- Record exception in OpenTelemetry span
- Skip affected dataset
- Continue harvesting

## Integration Points

### m4.2_basic_middleware → m4.2_middleware_harvester

The `m4.2_basic_middleware` project handles:

- Sitemap fetching and parsing
- HTML extraction
- Embedded JSON-LD extraction
- Writing harvested JSON to files

The `m4.2_middleware_harvester` (this repository) handles:

- Reading harvested JSON files
- Mapping Schema.org Dataset to ARC objects
- Generating RO-Crate JSON-LD output
- Integration with the central Harvester orchestrator

### Recommended Integration Pattern

```yaml
# Step 1: Run basic_middleware to harvest JSON
# Output: /path/to/harvested/openagrar.json

# Step 2: Run middleware_harvester with schema_org plugin
schema_org:
  json_source_url: "/path/to/harvested/openagrar.json"
  json_source_type: "file"
  source_identifier: "openagrar"
```
