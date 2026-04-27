"""Plugin generator for Schema.org-to-ARC harvesting.

Exposes `run_plugin`, the `AsyncGenerator` integration point consumed by the
central Harvester orchestrator. This module contains no CLI entry point.
"""

import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import cast

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.harvester.plugin_config import PluginConfig
from middleware.schema_org.config import Config
from middleware.schema_org.errors import SchemaOrgFetchError, SchemaOrgParseError
from middleware.schema_org.mapper import SchemaOrgMapper
from middleware.schema_org.models import SchemaOrgDataset

logger = logging.getLogger(__name__)


async def run_plugin(config: PluginConfig) -> AsyncGenerator[str | HarvesterError, None]:
    """Run the harvest process and yield serialized RO-Crate ARCs or Harvester errors."""
    schema_org_config = cast(Config, config)

    # 1. Setup Mapper
    mapper = SchemaOrgMapper()

    # 2. Fetch and process JSON data
    count = 0

    try:
        # Fetch JSON data based on source type
        json_data = await fetch_json_data(schema_org_config)

        if not isinstance(json_data, list):
            yield RecordProcessingError("JSON data must be a list of datasets", "root", None)
            return

        for item in json_data:
            try:
                # Parse as SchemaOrgDataset
                dataset = SchemaOrgDataset.model_validate(item)

                # Map to ARC
                arc = mapper.map_dataset(dataset)

                # Yield serialized ARC
                json_str = arc.ToROCrateJsonString()
                yield json_str

                logger.info("Successfully generated ARC for dataset: %s", dataset.name or dataset.id)
                count += 1

            except Exception as e:  # noqa: BLE001
                dataset_id = str(item.get("@id", item.get("id", "unknown"))) if isinstance(item, dict) else "unknown"
                yield RecordProcessingError(f"Failed to map dataset: {e}", dataset_id, e)
                continue

        logger.info("Harvest generator exhausted. Processed %d datasets.", count)

    except (RuntimeError, ValueError) as e:
        logger.error("Harvest failed: %s", e)


async def fetch_json_data(config: Config) -> list | dict:
    """Fetch JSON data based on configuration.

    Args:
        config: Schema.org plugin configuration

    Returns:
        Parsed JSON data

    Raises:
        SchemaOrgFetchError: If fetching fails
        SchemaOrgParseError: If JSON parsing fails
    """
    if config.json_source_type == "url":
        return await fetch_from_url(config.json_source_url, config.timeout)
    elif config.json_source_type == "file":
        return fetch_from_file(config.json_source_url)
    elif config.json_source_type == "directory":
        return fetch_from_directory(config.json_source_url)
    else:
        raise SchemaOrgFetchError(f"Unknown source type: {config.json_source_type}")


async def fetch_from_url(url: str, timeout: int) -> list | dict:
    """Fetch JSON data from HTTP URL."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPError as e:
        raise SchemaOrgFetchError(f"Failed to fetch JSON from URL: {e}") from e
    except json.JSONDecodeError as e:
        raise SchemaOrgParseError(f"Failed to parse JSON response: {e}") from e


def fetch_from_file(file_path: str) -> list | dict:
    """Fetch JSON data from local file."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise SchemaOrgFetchError(f"File not found: {file_path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        raise SchemaOrgParseError(f"Failed to parse JSON file: {e}") from e


def fetch_from_directory(dir_path: str) -> list | dict:
    """Fetch and merge JSON data from directory.

    Reads all .json files in the directory and returns them as a combined list.
    """
    try:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            raise SchemaOrgFetchError(f"Directory not found: {dir_path}")

        all_data = []
        for json_file in path.glob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)

        return all_data
    except json.JSONDecodeError as e:
        raise SchemaOrgParseError(f"Failed to parse JSON file in directory: {e}") from e
