"""DCAT-AP catalog Protocol implementation (Hydra pagination, e.g. CKAN ``ckanext-dcat``).

Fetches a Hydra-paginated DCAT-AP JSON-LD catalog (a JSON-LD document per page,
with a ``hydra:PagedCollection`` node carrying ``hydra:nextPage``). Each page is
parsed into an rdflib ``Graph`` once; for every ``dcat:Dataset`` on that page a
small per-dataset subgraph is extracted (Concise Bounded Description plus one
hop into referenced distributions/publisher/contact point/spatial coverage) and
yielded as an inline ``JsonLdDiscoveryResult``.

This Protocol only splits the catalog into records; parsing the record payload
is the ``jsonld`` PayloadParser's job and vocabulary mapping is the DataMapper's.
Nothing here is RDI-specific: the catalog URL is ``config.sitemap_url``.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.generic.config import ProtocolType
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult

DCAT = Namespace("http://www.w3.org/ns/dcat#")
HYDRA = Namespace("http://www.w3.org/ns/hydra/core#")

# Predicates whose named-resource objects get their own CBD folded into the
# per-dataset subgraph. The dataset's own CBD already recurses into blank
# nodes (contactPoint / spatial are typically blank nodes in ckanext-dcat
# output), so this only adds real triples for the named-resource case.
_EXTEND_PREDICATES: tuple[URIRef, ...] = (
    DCAT.distribution,
    DCTERMS.publisher,
    DCAT.contactPoint,
    DCTERMS.spatial,
)


@Protocol.register(ProtocolType.dcat_ap)
class DcatApProtocol(Protocol):
    """Protocol for Hydra-paginated DCAT-AP catalogs (e.g. CKAN's ``ckanext-dcat``)."""

    async def get_expected_count(self) -> int | None:
        """Return ``hydra:totalItems`` from the first catalog page, if present."""
        page_graph = await self._fetch_page_graph(self.config.sitemap_url, self._client)
        totals = list(page_graph.objects(None, HYDRA.totalItems))
        if not totals:
            return None
        try:
            return int(str(totals[0]))
        except ValueError:
            return None

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        url: str | None = self.config.sitemap_url
        visited: set[str] = set()
        while url:
            if url in visited:
                raise GenericProtocolError(f"DCAT-AP catalog pagination loop detected at {url}")
            visited.add(url)

            page_graph = await self._fetch_page_graph(url, client)
            dataset_subjects = sorted(
                (s for s in page_graph.subjects(RDF.type, DCAT.Dataset) if isinstance(s, URIRef)),
                key=str,
            )
            for subject in dataset_subjects:
                subgraph = self._extract_dataset_subgraph(page_graph, subject)
                yield JsonLdDiscoveryResult(identifier=str(subject), payload=self._graph_to_jsonld(subgraph))

            url = self._next_page_url(page_graph)

    async def _fetch_page_graph(self, url: str, client: NiceHttpClient) -> Graph:
        try:
            response = await client.get_with_policy(url)
            text = response.text
            graph = Graph()
            if len(text.encode("utf-8")) >= self._parse_threshold_bytes():
                await asyncio.to_thread(graph.parse, data=text, format="json-ld")
            else:
                graph.parse(data=text, format="json-ld")
            return graph
        except Exception as exc:  # noqa: BLE001
            raise GenericProtocolError(f"Failed to fetch/parse DCAT-AP catalog page {url}: {exc}") from exc

    def _parse_threshold_bytes(self) -> int:
        return int(getattr(self.config, "jsonld_parse_threshold_bytes", 65536))

    @staticmethod
    def _next_page_url(graph: Graph) -> str | None:
        for value in graph.objects(None, HYDRA.nextPage):
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _extract_dataset_subgraph(full_graph: Graph, subject: URIRef) -> Graph:
        """Return the dataset's CBD plus one hop into ``_EXTEND_PREDICATES`` objects."""
        small = Graph()
        full_graph.cbd(subject, target_graph=small)
        for predicate in _EXTEND_PREDICATES:
            for obj in full_graph.objects(subject, predicate):
                full_graph.cbd(obj, target_graph=small)
        return small

    @staticmethod
    def _graph_to_jsonld(graph: Graph) -> dict[str, object]:
        """Serialize ``graph`` to expanded JSON-LD (no ``@context``) wrapped in ``@graph``."""
        nodes = json.loads(graph.serialize(format="json-ld"))
        return {"@graph": nodes}
