# Schema.org to ARC Harvester Plugin

This plugin harvests Schema.org metadata from JSON sources and converts it to ARC (Annotated Research Context) format for the FAIRagro Middleware.

## Features

- **Multiple Source Types**: Fetch Schema.org JSON from URLs, local files, or directories
- **Schema.org Dataset Support**: Maps Schema.org Dataset objects to ARC Investigation/Study/Assay structure
- **Provider Extensions**: Supports datasets from EDAL, BONARES, OpenAgris, Publisso, Thünen Atlas
- **BioSchemas Compatible**: Works with BioSchemas Dataset profile

## Installation

The plugin is part of the FAIRagro Middleware Harvester workspace. Install dependencies with:

```bash
uv sync --dev --all-packages
```

## Configuration

Add a `schema_org` entry to your harvester configuration file:

```yaml
api_client:
  base_url: "https://api.fairagro.net"
  # ... auth configuration ...

repositories:
  - rdi: "edal-datasets"
    schema_org:
      json_source_url: "https://example.com/datasets.json"
      json_source_type: "url"
      timeout: 60
```

### Configuration Options

| Parameter | Type | Required | Default | Description |
| --------- | ---- | -------- | ------- | ----------- |
| `json_source_url` | string | Yes | - | URL or path to the Schema.org JSON source |
| `json_source_type` | string | No | "url" | Type of source: "url", "file", or "directory" |
| `source_identifier` | string | No | null | Optional identifier to filter sources |
| `timeout` | int | No | 30 | Request timeout in seconds |
| `batch_size` | int | No | 50 | Number of records to process per batch |

### Source Type Examples

**URL Source:**

```yaml
schema_org:
  json_source_url: "https://api.example.org/datasets"
  json_source_type: "url"
```

**File Source:**

```yaml
schema_org:
  json_source_url: "/path/to/datasets.json"
  json_source_type: "file"
```

**Directory Source:**

```yaml
schema_org:
  json_source_url: "/path/to/json/files/"
  json_source_type: "directory"
```

## Usage

Run the harvester with the configuration file:

```bash
uv run python -m middleware.harvester.main -c config.yaml
```

## Architecture

The plugin follows the FAIRagro harvester plugin architecture:

1. **Plugin Module** (`plugin.py`): Exposes `run_plugin()` async generator
2. **Mapper Module** (`mapper.py`): Converts Schema.org Dataset to ARC
3. **Models Module** (`models.py`): Pydantic models for Schema.org types
4. **Config Module** (`config.py`): Configuration validation
5. **Errors Module** (`errors.py`): Custom exception hierarchy

## Testing

Run tests with pytest:

```bash
uv run pytest middleware/schema_org/tests/ -v
```

## Mapping Documentation

See the specification documents for detailed mapping information:

- [Harvesting Specification](spec/schema-org-harvesting/spec.md)
- [Harvesting Design](spec/schema-org-harvesting/design.md)
- [Mapping Specification](spec/schema-org-to-arc-mapping/spec.md)
- [Mapping Design](spec/schema-org-to-arc-mapping/design.md)

## License

This plugin is part of the FAIRagro Middleware project.
