# FAIRagro INSPIRE-to-ARC Middleware

This repository contains the INSPIRE-to-ARC harvesting middleware. It harvests geospatial metadata from INSPIRE-compliant CSW (Catalogue Service for the Web) endpoints and converts them into ARC objects, which are then uploaded to the FAIRagro Middleware API.

## 🚀 Usage Examples

### Basic Querying

```python
from middleware.inspire_to_arc.harvester import CSWClient

# Connect to GDI-DE CSW
client = CSWClient("https://gdk.gdi-de.org/gdi-de/srv/eng/csw")
client.connect()

# Fetch records
records = list(client.get_records(max_records=10))
```

### Advanced Filtering with FES

Use OWSLib's Filter Encoding Specification (FES) for readable, type-safe queries:

```python
from owslib.fes import And, PropertyIsEqualTo, PropertyIsLike

# Query for weather radar data from DWD
constraints = [
    And([
        PropertyIsLike("AnyText", "*radar*"),
        PropertyIsEqualTo("OrganisationName", "Deutscher Wetterdienst"),
    ])
]

records = list(client.get_records(constraints=constraints, max_records=100))
```

### Raw XML Queries

For complex queries, you can also use raw XML:

```python
xml_request = b"""<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
                service="CSW" version="2.0.2">
  <csw:Query typeNames="csw:Record">
    <csw:ElementSetName>full</csw:ElementSetName>
  </csw:Query>
</csw:GetRecords>"""

records = list(client.get_records(xml_request=xml_request))
```

## 🏗 Architecture

The middleware consists of three main layers:

1. **Orchestrator (`main.py`):** Manages the processing loop, configuration loading, and interaction with the API Client.
2. **Harvester (`harvester.py`):** Interaction layer with CSW endpoints using `owslib`. It parses ISO 19139 XML records into an internal `InspireRecord` Pydantic model.
3. **Mapper (`mapper.py`):** Specialized logic for translating INSPIRE/ISO fields into ARC objects (Investigation, Study, Assay) using `arctrl`.

Detailed documentation can be found in [docs/ARCHITECTURAL_DESIGN.md](docs/ARCHITECTURAL_DESIGN.md).

## 🗺 Mapping Documentation

The detailed strategy for mapping INSPIRE/ISO 19139 fields to the ISA model (Investigation, Study, Assay) is documented in:
👉 **[docs/mapping.md](docs/mapping.md)**

## 📁 Project Structure

- `middleware/inspire_to_arc`: The core harvesting and mapping logic.
- `docker/`: Dockerfiles and container structure tests.
- `dev_environment/`: Local development setup with Docker Compose.
- `scripts/`: Quality check and utility scripts.

## 📊 Implementation Status

**Current**: ~10 fields mapped (basic identification, contacts, lineage, extent, constraints).
**Planned**: 50+ fields mapped with a comprehensive protocol-based approach.
