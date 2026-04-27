# Schema.org Harvesting - Design

## Architecture

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

### Error Handling

The plugin uses a custom exception hierarchy:
- `SchemaOrgHarvesterError`: Base exception
- `SchemaOrgFetchError`: Fetch failures (network, file not found)
- `SchemaOrgParseError`: JSON parsing failures

Errors are yielded as `RecordProcessingError` instances to allow the orchestrator to continue processing other records.

## Data Flow

1. **Configuration Loading**: The harvester loads the YAML config and validates it against the `Config` Pydantic model
2. **Plugin Selection**: Based on the `schema_org` key in the repository config, the orchestrator selects the `run_schema_org_plugin` function
3. **Data Fetching**: The plugin fetches JSON data based on the configured source type
4. **Dataset Parsing**: Each JSON object is validated against the `SchemaOrgDataset` model
5. **ARC Mapping**: The mapper converts each dataset to an ARC object
6. **Serialization**: The ARC is serialized to RO-Crate JSON-LD format
7. **Upload**: The orchestrator uploads the ARC to the configured RDI via the API client