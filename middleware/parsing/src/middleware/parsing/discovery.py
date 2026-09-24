"""Discovery unit types shared by Protocol implementations and parsers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiscoveryResult:
    """Base class for results yielded by Protocol discovery.

    Every discovery result carries a stable ``identifier`` used for
    deduplication in ``Protocol.discover()`` and for error reporting.
    Concrete subclasses fill it with a URL, a Regal ``@id``, or another
    provider-specific key.
    """

    identifier: str


@dataclass
class UrlDiscoveryResult(DiscoveryResult):
    """Discovery result representing a dataset URL.

    The ``identifier`` is the dataset URL. When the protocol knows a native
    catalog id for the harvested record (e.g. MyCoRe Solr ``id``), it MAY
    supply ``harvest_source_id`` for stable Schema.org mapping.
    """

    harvest_source_id: str | None = None

    @property
    def url(self) -> str:
        """The discovered dataset URL (alias for ``identifier``)."""
        return self.identifier


@dataclass
class JsonLdDiscoveryResult(DiscoveryResult):
    """Discovery result carrying an inline JSON-LD record payload."""

    payload: dict[str, object]


@dataclass
class XmlDiscoveryResult(DiscoveryResult):
    """Discovery result carrying inline XML (e.g. OAI ``<metadata>`` RDF/XML)."""

    xml: str
