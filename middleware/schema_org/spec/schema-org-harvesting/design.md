# Schema.org Harvesting - Design

## Overview

This document describes the design of the Schema.org harvesting system. It covers both:

1. **Direct JSON harvesting** (this repository) - Processing pre-aggregated JSON-LD sources
2. **Sitemap-based harvesting** (m4.2_basic_middleware) - Full RDI harvesting with sitemap parsing and embedded JSON-LD extraction

## Architecture

### Direct JSON Harvesting (this repository)

The Schema.org harvester plugin follows the same plugin architecture as the INSPIRE plugin:

```
┌─────────────────────────────────────────────────────────────┐
│                    Harvester Orchestrator                    │
│  (middleware/harvester/src/middleware/harvester/main.py)    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ AsyncGenerator[str | HarvesterError]
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   run_plugin() Generator                     │
│  (middleware/schema_org/src/middleware/schema_org/plugin.py)│
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ fetch_json_  │───▶│ SchemaOrg    │───▶│ SchemaOrg    │  │
│  │ data()       │    │ Dataset      │    │ Mapper       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ ARC JSON (RO-Crate)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              FAIRagro Middleware API Client                  │
└─────────────────────────────────────────────────────────────┘
```

### Sitemap-Based Harvesting (m4.2_basic_middleware)

The full harvesting pipeline with sitemap support:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    MetadataScraper                               │
│  (m4.2_basic_middleware/middleware/metadata_scraper/__init__.py)│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  SitemapParser   │  │ MetadataExtractor│  │ HttpSession  │  │
│  │  (Abstract)      │  │ (Abstract)       │  │              │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘  │
│           │                     │                                │
│           │ datasets            │ metadata                       │
│           │ Iterator[str]       │ List[Dict]                     │
│           ▼                     ▼                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Harvested JSON Output                       │    │
│  │         /path/to/harvested/{repo_name}.json              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JSON file
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              m4.2_middleware_harvester                       │
│  (this repository - schema_org plugin)                       │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ fetch_from_  │───▶│ SchemaOrg    │───▶│ SchemaOrg    │  │
│  │ file()       │    │ Dataset      │    │ Mapper       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
│  ┌──────────────┐                                           │
│  │ ARC JSON     │                                           │
│  │ (RO-Crate)   │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Plugin Module (`plugin.py`)

The plugin module exposes the `run_plugin()` async generator function that:

1. Fetches JSON data from the configured source
2. Parses each item as a `SchemaOrgDataset`
3. Maps the dataset to ARC using `SchemaOrgMapper`
4. Yields the serialized RO-Crate JSON string

### Fetch Functions

- `fetch_from_url()`: Async HTTP fetch using `httpx`
- `fetch_from_file()`: Synchronous local file read
- `fetch_from_directory()`: Merges multiple JSON files from a directory

### SitemapParser Hierarchy (m4.2_basic_middleware)

```python
# Abstract base class
class SitemapParser(RegisteringABC):
    @property
    def datasets(self) -> Iterator[str]: ...
    @property
    def has_metadata(self) -> bool: ...
    def get_metadata(self) -> List[Dict]: ...

# Implementations
class SitemapParserXml(SitemapParser):
    """Parses XML sitemaps (sitemaps.org standard)"""

class SitemapParserOpenAgrar(SitemapParser):
    """Parses OpenAgrar JSON sitemap format"""

class SitemapParserPublisso(SitemapParser):
    """Parses Publisso sitemap format"""

class SitemapParserThunenAtlas(SitemapParser):
    """Parses Thünen Atlas sitemap format"""
```

### MetadataExtractor Hierarchy (m4.2_basic_middleware)

```python
# Abstract base class
class MetadataExtractor(RegisteringABC):
    @abstractmethod
    def metadata(self, content: str, url: str) -> List[Dict]: ...
    
    @abstractmethod
    def raw_metadata(self, content: str) -> List[str]: ...

# Implementation for embedded JSON-LD
class MetadataExtractorEmbeddedJsonld(MetadataExtractor):
    """Extracts JSON-LD from HTML <script> tags using extruct"""
    
    def metadata(self, content: str, url: str) -> List[Dict]:
        metadata = extract(content, base_url=url, syntaxes=['json-ld'])
        return metadata['json-ld']
```

### Error Handling

The plugin uses a custom exception hierarchy:

- `SchemaOrgHarvesterError`: Base exception
- `SchemaOrgFetchError`: Fetch failures (network, file not found)
- `SchemaOrgParseError`: JSON parsing failures

Errors are yielded as `RecordProcessingError` instances to allow the orchestrator to continue processing other records.

### Error Handling (m4.2_basic_middleware)

```python
class SitemapParseError(RuntimeError):
    """Raised when sitemap parsing fails"""

class MetadataParseError(RuntimeError):
    """Raised when metadata extraction fails"""

class HttpSessionFetchError(RuntimeError):
    """Raised when HTTP fetch fails"""

class HttpSessionDecodeError(RuntimeError):
    """Raised when content decoding fails"""
```

## Data Flow

### Direct JSON Source (this repository)

1. **Configuration Loading**: The harvester loads the YAML config and validates it against the `Config` Pydantic model
2. **Plugin Selection**: Based on the `schema_org` key in the repository config, the orchestrator selects the `run_schema_org_plugin` function
3. **Data Fetching**: The plugin fetches JSON data based on the configured source type
4. **Dataset Parsing**: Each JSON object is validated against the `SchemaOrgDataset` model
5. **ARC Mapping**: The mapper converts each dataset to an ARC object
6. **Serialization**: The ARC is serialized to RO-Crate JSON-LD format
7. **Upload**: The orchestrator uploads the ARC to the configured RDI via the API client

### Sitemap-Based Harvesting (Two-Stage Pipeline)

#### Stage 1: m4.2_basic_middleware

1. Load sitemap configuration from YAML
2. Fetch sitemap content (XML/JSON/Text)
3. Parse sitemap to extract dataset URLs
4. For each URL:
   - Fetch HTML content
   - Extract embedded JSON-LD
   - Filter for `@type: "Dataset"`
5. Write harvested JSON to file: `/path/to/harvested/{repo_name}.json`
6. Commit to Git repository (optional)

#### Stage 2: m4.2_middleware_harvester

1. Load harvested JSON file via `json_source_type: "file"`
2. Parse as `SchemaOrgDataset` objects
3. Map to ARC using `SchemaOrgMapper`
4. Generate RO-Crate JSON-LD
5. Upload to API

## Configuration Examples

### Direct JSON Harvesting

```yaml
schema_org:
  json_source_url: "https://example.com/datasets.json"
  json_source_type: "url"
  timeout: 60
  batch_size: 50
```

### Sitemap-Based Harvesting (m4.2_basic_middleware)

```yaml
sitemaps:
  - name: "openagrar"
    url: "https://www.openagrar.de/sitemap.json"
    sitemap: "openagrar"
    metadata: "embedded_jsonld"
    http_client:
      timeout: 30
      headers:
        User-Agent: "FAIRagro Middleware Harvester"
```

### Combined Pipeline

```yaml
# Step 1: Run basic_middleware
# Command: python -m middleware.main --config config_harvest.yml
# Output: /data/harvested/openagrar.json

# Step 2: Run middleware_harvester
# config.yaml:
schema_org:
  json_source_url: "/data/harvested/openagrar.json"
  json_source_type: "file"
  source_identifier: "openagrar"
```

## Implementation Details

### SitemapParserXml

```python
class SitemapParserXml(SitemapParser):
    @property
    def datasets(self) -> Iterator[str]:
        xml_root = ElementTree.fromstring(self.content)
        for loc in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            if loc.text is not None:
                yield loc.text
```

### MetadataExtractorEmbeddedJsonld

```python
class MetadataExtractorEmbeddedJsonld(MetadataExtractor):
    def metadata(self, content: str, url: str) -> List[Dict]:
        base_url = get_base_url(content, url)
        metadata = extract(content, base_url=base_url, uniform=True, syntaxes=['json-ld'])
        return metadata['json-ld']
    
    def raw_metadata(self, content: str) -> List[str]:
        soup = BeautifulSoup(content, 'html.parser')
        json_ld = soup.find_all('script', type='application/ld+json')
        return [js.text for js in json_ld]
```

## Dependencies

### This Repository

```python
from arctrl import ARC, ArcInvestigation, ArcStudy, ArcAssay, ...
from pydantic import BaseModel, Field
import httpx
```

### m4.2_basic_middleware

```python
from extruct import extract  # JSON-LD extraction from HTML
from bs4 import BeautifulSoup  # HTML parsing
from w3lib.html import get_base_url  # Base URL extraction
from xml.etree import ElementTree  # XML parsing
import aiofiles  # Async file I/O
import yaml  # Configuration
```

## Testing Strategy

### Unit Tests (this repository)

- Test `SchemaOrgMapper` with various dataset structures
- Test `fetch_from_*` functions with mock data
- Test error handling for malformed JSON

### Unit Tests (m4.2_basic_middleware)

- Test `SitemapParserXml` with sample XML sitemaps
- Test `SitemapParserOpenAgrar` with sample JSON sitemaps
- Test `MetadataExtractorEmbeddedJsonld` with sample HTML
- Test error handling for invalid formats

### Integration Tests

- End-to-end harvesting from real RDI endpoints
- Full pipeline: sitemap → JSON → ARC → RO-Crate
