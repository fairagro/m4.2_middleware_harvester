# Schema.org Dataset Abstraction — Design

## Architecture overview

The dataset abstraction separates payload handling from sitemap discovery and mapping. Each dataset wrapper exposes a stable identifier and produces an `rdflib.Graph` representation of the payload.

## Key Decisions

1. **Isolate dataset wrappers in `dataset.py`**
   — This keeps provider-specific payload parsing separate from higher-level plugin orchestration.

2. **Register dataset implementations by `DatasetType`**
   — A registry allows the plugin factory to select the correct implementation without branching logic.

3. **Use the dataset identifier as the stable processing key**
   — The identifier is used for error reporting, deduplication, and downstream mapping.
