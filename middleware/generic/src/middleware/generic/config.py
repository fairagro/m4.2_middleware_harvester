"""Configuration model for the generic harvest plugin."""

from __future__ import annotations

import logging
from typing import Annotated, Self, cast
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from middleware.contracts.nice_http_client import NiceHttpClientConfig
from middleware.generic.protocol.dcat_ap import DcatApProtocolConfig
from middleware.generic.protocol.mycore_solr import MycoreSolrProtocolConfig
from middleware.generic.protocol.protocol import ProtocolType, ProtocolTypeConfig
from middleware.generic.protocol.pubplant_json_array import PubPlantJsonArrayProtocolConfig
from middleware.generic.protocol.regal_find import RegalFindProtocolConfig
from middleware.generic.protocol.xml import XmlProtocolConfig

logger = logging.getLogger(__name__)

_LEGACY_THRESHOLD_MSG = (
    "generic.jsonld_parse_threshold_bytes is deprecated and no longer applies to payload parsing; "
    "set parser.jsonld_parse_threshold_bytes and/or protocol.dcat_ap.jsonld_parse_threshold_bytes instead."
)

_PROTOCOL_TYPE_FIELDS = frozenset({
    "xml",
    "mycore_solr",
    "dcat_ap",
    "pubplant_json_array",
    "regal_find",
})


class ProtocolConfig(BaseModel):
    """Shared transport plus exactly one type-named Protocol config child."""

    model_config = ConfigDict(populate_by_name=True)

    http: Annotated[
        NiceHttpClientConfig,
        Field(
            description="HTTP client settings used by Protocol discovery.",
            default_factory=lambda: NiceHttpClientConfig(respect_robots_txt=True),
        ),
    ]
    xml: Annotated[
        XmlProtocolConfig | None,
        Field(description="XML sitemap Protocol config."),
    ] = None
    mycore_solr: Annotated[
        MycoreSolrProtocolConfig | None,
        Field(description="MyCoRe Solr Protocol config."),
    ] = None
    dcat_ap: Annotated[
        DcatApProtocolConfig | None,
        Field(description="DCAT-AP catalog Protocol config."),
    ] = None
    pubplant_json_array: Annotated[
        PubPlantJsonArrayProtocolConfig | None,
        Field(description="PubPlant JSON array Protocol config."),
    ] = None
    regal_find: Annotated[
        RegalFindProtocolConfig | None,
        Field(description="Regal /find Protocol config."),
    ] = None

    @model_validator(mode="after")
    def exactly_one_protocol_type(self) -> Self:
        """Require exactly one registered type-named config child."""
        set_fields = [name for name in _PROTOCOL_TYPE_FIELDS if getattr(self, name) is not None]
        if len(set_fields) != 1:
            raise ValueError(
                f"generic.protocol must set exactly one of {sorted(_PROTOCOL_TYPE_FIELDS)}; got: {set_fields or 'none'}"
            )
        return self

    @property
    def protocol_type(self) -> ProtocolType:
        """Active Protocol registry key (the single set type-named child)."""
        return ProtocolType(next(name for name in _PROTOCOL_TYPE_FIELDS if getattr(self, name) is not None))

    @property
    def type_config(self) -> ProtocolTypeConfig:
        """Config model for the active Protocol type."""
        return cast(ProtocolTypeConfig, getattr(self, self.protocol_type.value))


class Config(BaseModel):
    """Configuration for the generic Protocol + shared PayloadParser plugin.

    Protocol selection uses nested ``protocol:`` (shared ``http`` plus exactly one
    type-named child). Shared parser selection uses the repository-level ``parser:``
    block.
    """

    model_config = ConfigDict(populate_by_name=True)

    protocol: Annotated[
        ProtocolConfig | None,
        Field(description="Nested Protocol config (shared http + one type-named child)."),
    ] = None
    jsonld_parse_threshold_bytes: Annotated[
        int | None,
        Field(
            description=(
                "Deprecated. Use parser.jsonld_parse_threshold_bytes (payload parsing) and "
                "protocol.dcat_ap.jsonld_parse_threshold_bytes (catalog pages) instead."
            ),
            deprecated=True,
            ge=1,
        ),
    ] = None
    resource_base_url: Annotated[
        str | None,
        Field(
            description=(
                "Optional base URL for expanding compact resource ids. "
                "If unset, derived as `{scheme}://{host}/resource/` from the active "
                "protocol type's `entry_url` when that field exists."
            ),
        ),
    ] = None
    worker_tasks: Annotated[
        int | None,
        Field(
            description=(
                "Number of worker tasks consuming discovery results. "
                "If unset, defaults to the HTTP max_connections value."
            ),
            ge=1,
        ),
    ] = None

    @model_validator(mode="after")
    def require_nested_protocol(self) -> Self:
        """Require nested ``protocol``; warn on deprecated threshold field."""
        if self.__dict__.get("jsonld_parse_threshold_bytes") is not None:
            logger.warning(_LEGACY_THRESHOLD_MSG)
        if self.protocol is None:
            raise ValueError("generic config requires nested protocol: { http, <type>: { entry_url } }")
        return self

    @property
    def effective_protocol(self) -> ProtocolConfig:
        """Nested protocol config (always set post-validation)."""
        if self.protocol is None:
            raise ValueError("generic.protocol is unset; config validation did not run")
        return self.protocol

    @property
    def active_protocol_type(self) -> ProtocolType:
        """Active Protocol type key."""
        return self.effective_protocol.protocol_type

    @property
    def effective_worker_tasks(self) -> int:
        """Configured worker tasks or fall back to the HTTP client's max connections."""
        return self.worker_tasks or self.effective_protocol.http.max_connections

    @property
    def effective_resource_base_url(self) -> str:
        """Configured resource base URL or derive it from the active type's entry_url."""
        if self.resource_base_url is not None and self.resource_base_url.strip():
            return self._normalize_resource_base_url(self.resource_base_url)
        entry_url = getattr(self.effective_protocol.type_config, "entry_url", None)
        if not isinstance(entry_url, str) or not entry_url.strip():
            raise ValueError(
                "Cannot derive resource_base_url: set resource_base_url or use a protocol type with entry_url"
            )
        return self._resource_base_url_from_entry(entry_url)

    @staticmethod
    def _normalize_resource_base_url(url: str) -> str:
        return url.rstrip("/") + "/"

    @staticmethod
    def _resource_base_url_from_entry(entry_url: str) -> str:
        parsed = urlparse(entry_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Cannot derive resource_base_url from entry URL: {entry_url}")
        return f"{parsed.scheme}://{parsed.netloc}/resource/"
