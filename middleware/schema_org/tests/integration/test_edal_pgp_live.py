"""Live end-to-end integration test for EDAL-PGP harvester.

This test requires network access to https://doi.ipk-gatersleben.de/sitemap.xml
and the actual DOI landing pages. It is skipped by default.

Run with: uv run pytest middleware/schema_org/tests/integration/test_edal_pgp_live.py -v --network
"""

import os

import pytest

from middleware.schema_org.config import (
    Config,
    DatasetType,
    NiceHttpClientConfig as SchemaOrgNiceHttpClientConfig,
    PayloadType,
    SitemapType,
)
from middleware.schema_org.plugin import SchemaOrgPlugin

pytestmark = pytest.mark.skipif(
    os.environ.get("NETWORK_ENABLED") != "1",
    reason="Live network test; set NETWORK_ENABLED=1 to run",
)


@pytest.mark.asyncio
async def test_edal_pgp_live_pipeline() -> None:
    """Hit the live EDAL-PGP endpoint and verify the full pipeline succeeds for at least one dataset."""
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(),
    )

    results: list[str] = []
    async for item in SchemaOrgPlugin(config).run():
        if isinstance(item, str):
            results.append(item)

    assert len(results) >= 1, "Expected at least one successfully harvested dataset from the live endpoint"
