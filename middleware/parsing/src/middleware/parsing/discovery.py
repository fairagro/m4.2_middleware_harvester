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

    The ``identifier`` is the dataset landing URL (identity / ``source_url``).
    When the protocol knows a native catalog id for the harvested record
    (e.g. MyCoRe ``id``), it MAY supply ``harvest_source_id``. When the
    machine-readable payload lives at a different URL (e.g. MyCoRe REST
    object XML), it MAY supply ``fetch_url``; fetching parsers use
    ``request_url`` (``fetch_url`` when set, else ``url``).
    """

    harvest_source_id: str | None = None
    fetch_url: str | None = None

    @property
    def url(self) -> str:
        """The discovered dataset landing URL (alias for ``identifier``)."""
        return self.identifier

    @property
    def request_url(self) -> str:
        """URL to fetch for the payload (``fetch_url`` when set, else ``url``)."""
        if self.fetch_url is not None and self.fetch_url.strip():
            return self.fetch_url.strip()
        return self.identifier


@dataclass
class JsonLdDiscoveryResult(DiscoveryResult):
    """Discovery result carrying an inline JSON-LD record payload.

    When the protocol knows a native record id distinct from the RDF
    subject's own IRI (e.g. a composite dedup key), it MAY supply
    ``harvest_source_id`` for stable Schema.org mapping, mirroring
    ``UrlDiscoveryResult.harvest_source_id``.
    """

    payload: dict[str, object]
    harvest_source_id: str | None = None


@dataclass
class XmlDiscoveryResult(DiscoveryResult):
    """Discovery result carrying inline XML (e.g. OAI ``<metadata>`` RDF/XML)."""

    xml: str
