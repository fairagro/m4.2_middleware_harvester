# Schema.org Harvesting

## Requirements

- [ ] Support fetching Schema.org JSON data from multiple source types:
  - [ ] HTTP/HTTPS URLs (API endpoints, JSON files)
  - [ ] Local file paths
  - [ ] Directory paths (merge multiple JSON files)
- [ ] Parse JSON-LD context and extract Schema.org Dataset objects
- [ ] Handle batch processing of multiple datasets from a single source
- [ ] Support provider-specific filtering via `source_identifier` configuration
- [ ] Implement timeout configuration for HTTP requests
- [ ] Handle JSON parsing errors gracefully with appropriate error reporting

## Configuration

The plugin uses the following configuration parameters:

| Parameter | Type | Required | Default | Description |
| --------- | ---- | -------- | ------- | ----------- |
| `json_source_url` | string | Yes | - | URL or path to the Schema.org JSON source |
| `json_source_type` | string | No | "url" | Type of source: "url", "file", or "directory" |
| `source_identifier` | string | No | null | Optional identifier to filter sources |
| `timeout` | int | No | 30 | Request timeout in seconds |
| `batch_size` | int | No | 50 | Number of records to process per batch |

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
