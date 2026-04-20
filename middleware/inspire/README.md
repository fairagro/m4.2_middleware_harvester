# INSPIRE-to-ARC Harvester Plugin

The INSPIRE plugin connects to standard-compliant Metadata Catalogues (CSW - Catalogue Service for the Web) and transforms ISO 19139 (Dublin Core and GMD) records into FAIRagro-compliant Annotated Research Context (ARC) objects.

## Overview

Designed for geo-spatial and environmental metadata integration, this plugin performs dual-pass harvesting:

1. **Identifier Fetch**: Retrieves a list of all record identifiers from the CSW using `brief` element set.
2. **Metadata Harvest**: Batches retrieval of full metadata records for conversion.

### Features

- Support for CSW 2.0.2.
- Conversion of INSPIRE/ISO 19139 metadata (Title, Abstract, Contacts, Dates, Spatial coverage).
- Robust XML parsing using OWSLib.

## Configuration

The plugin is configured as part of a `repository` entry in the central Harvester configuration.

### Full Plugin Configuration Reference

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `csw_url` | string | *(required)* | Base URL of the CSW 2.0.2 endpoint. |
| `cql_query` | string | `None` | OGC CQL filter (e.g., `AnyText LIKE '%agriculture%'`). |
| `xml_query` | string | `None` | Raw XML body for `GetRecords` (mutually exclusive with `cql_query`). |
| `chunk_size` | int | `50` | Number of records to fetch per paginated request. |
| `timeout` | int | `30` | Network timeout for CSW requests in seconds. |
| `max_records` | int | `None` | Debug limit: stop after N records (set to `None` for all). |

### Example Plugin Configuration

```yaml
repositories:
  - rdi: "my-csw-source"
    inspire:
      csw_url: "https://gdk.gdi-de.org/gdi-de/srv/eng/csw"
      chunk_size: 100
      cql_query: "AnyText LIKE '%soil%'"
```

## Mapping Logic

The transformation from INSPIRE records to ARCs follows specific mapping rules:

- **Identifier**: Used as the dataset ID in the ARC metadata.
- **Title**: Maps to the ARC investigation title.
- **Abstract**: Maps to the ARC investigation description.
- **Contacts**: Individual contacts are added as persons in the ARC investigation.

For a detailed breakdown of all mapping rules, please refer to the **[INSPIRE Mapping Specification](../../docs/mapping.md)**.

## External Documentation

- **[CSW 2.0.2 Standards](https://www.ogc.org/standard/cat/)**
- **[INSPIRE Metadata Guidelines](https://inspire.ec.europa.eu/metadata-codelist/MetadataDirectory)**
- **[ARCtrl API Reference](https://nfdi4plants.org/ARCtrl/)**
