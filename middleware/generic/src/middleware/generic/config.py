"""Configuration model for the generic harvest plugin."""

from __future__ import annotations

import logging
from typing import Annotated, Self, cast
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from middleware.generic.protocol.dcat_ap import DcatApProtocolConfig
from middleware.generic.protocol.mycore_solr import MycoreSolrProtocolConfig
from middleware.generic.protocol.protocol import ProtocolType, ProtocolTypeConfig
from middleware.generic.protocol.xml import XmlProtocolConfig
from middleware.harvester.nice_http_client import NiceHttpClientConfig

logger = logging.getLogger(__name__)

_LEGACY_FLAT_PROTOCOL_MSG = (
    "generic flat protocol_type/sitemap_url/http/page_size is deprecated; "
    "use nested protocol: { http: …, <type>: { entry_url: … } } instead. "
    "Support for the flat tree will be removed in a future release."
)

_LEGACY_THRESHOLD_MSG = (
    "generic.jsonld_parse_threshold_bytes is deprecated and no longer applies to payload parsing; "
    "set parser.jsonld_parse_threshold_bytes and/or protocol.dcat_ap.jsonld_parse_threshold_bytes instead."
)

_PROTOCOL_TYPE_FIELDS = frozenset({"xml", "mycore_solr", "dcat_ap"})


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

    Canonical protocol selection uses nested ``protocol:``. Flat
    ``protocol_type`` / ``sitemap_url`` / ``http`` / ``page_size`` remain as a
    deprecated lift path. Shared parser selection uses the repository-level
    ``parser:`` block.
    """

    model_config = ConfigDict(populate_by_name=True)

    protocol: Annotated[
        ProtocolConfig | None,
        Field(description="Nested Protocol config (shared http + one type-named child)."),
    ] = None
    protocol_type: Annotated[
        ProtocolType | None,
        Field(
            description="Deprecated. Use protocol.<type> instead.",
            deprecated=True,
        ),
    ] = None
    sitemap_url: Annotated[
        str | None,
        Field(
            description="Deprecated. Use protocol.<type>.entry_url instead.",
            deprecated=True,
        ),
    ] = None
    http: Annotated[
        NiceHttpClientConfig | None,
        Field(
            description="Deprecated. Use protocol.http instead.",
            deprecated=True,
        ),
    ] = None
    page_size: Annotated[
        int | None,
        Field(
            description="Deprecated. Use protocol.mycore_solr.page_size instead.",
            deprecated=True,
            ge=1,
        ),
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
    def lift_legacy_flat_protocol(self) -> Self:
        """Ensure ``protocol`` is set, lifting deprecated flat fields when needed."""
        flat_type = self.__dict__.get("protocol_type")
        flat_sitemap = self.__dict__.get("sitemap_url")
        flat_http = self.__dict__.get("http")
        flat_page_size = self.__dict__.get("page_size")
        flat_threshold = self.__dict__.get("jsonld_parse_threshold_bytes")
        flat_present = any(value is not None for value in (flat_type, flat_sitemap, flat_http, flat_page_size))

        if flat_threshold is not None:
            logger.warning(_LEGACY_THRESHOLD_MSG)

        if self.protocol is not None:
            if flat_present:
                self._assert_flat_agrees_with_protocol(
                    flat_type=flat_type,
                    flat_sitemap=flat_sitemap,
                    flat_http=flat_http,
                    flat_page_size=flat_page_size,
                )
                logger.warning(_LEGACY_FLAT_PROTOCOL_MSG)
            return self

        if flat_type is None or flat_sitemap is None:
            raise ValueError(
                "generic config requires nested protocol: { http, <type>: { entry_url } } "
                "or deprecated protocol_type + sitemap_url"
            )

        logger.warning(_LEGACY_FLAT_PROTOCOL_MSG)
        if flat_page_size is not None and flat_type is not ProtocolType.mycore_solr:
            raise ValueError(f"generic.page_size is not valid for protocol_type {flat_type.value} (no page_size field)")
        type_config: ProtocolTypeConfig
        http = flat_http if flat_http is not None else NiceHttpClientConfig(respect_robots_txt=True)
        if flat_type is ProtocolType.xml:
            type_config = XmlProtocolConfig(entry_url=flat_sitemap)
            nested = ProtocolConfig(http=http, xml=type_config)
        elif flat_type is ProtocolType.mycore_solr:
            type_config = MycoreSolrProtocolConfig(
                entry_url=flat_sitemap,
                page_size=flat_page_size if flat_page_size is not None else 200,
            )
            nested = ProtocolConfig(http=http, mycore_solr=type_config)
        elif flat_type is ProtocolType.dcat_ap:
            type_config = (
                DcatApProtocolConfig(entry_url=flat_sitemap)
                if flat_threshold is None
                else DcatApProtocolConfig(entry_url=flat_sitemap, jsonld_parse_threshold_bytes=flat_threshold)
            )
            nested = ProtocolConfig(http=http, dcat_ap=type_config)
        else:
            raise ValueError(f"Unsupported deprecated protocol_type: {flat_type}")

        # Assign in place: pydantic discards a returned copy when built via ``Config(...)``.
        self.protocol = nested
        return self

    def _assert_flat_agrees_with_protocol(
        self,
        *,
        flat_type: ProtocolType | None,
        flat_sitemap: str | None,
        flat_http: NiceHttpClientConfig | None,
        flat_page_size: int | None,
    ) -> None:
        assert self.protocol is not None
        if flat_type is not None and flat_type != self.protocol.protocol_type:
            raise ValueError(
                f"generic.protocol_type {flat_type!r} conflicts with protocol.{self.protocol.protocol_type.value}"
            )
        type_config = self.protocol.type_config
        flat_entry = getattr(type_config, "entry_url", None)
        if flat_sitemap is not None and flat_entry is not None and flat_sitemap != flat_entry:
            raise ValueError(f"generic.sitemap_url {flat_sitemap!r} conflicts with protocol entry_url {flat_entry!r}")
        if flat_sitemap is not None and flat_entry is None:
            raise ValueError(
                f"generic.sitemap_url {flat_sitemap!r} set but protocol.{self.protocol.protocol_type.value} "
                "has no entry_url"
            )
        if flat_http is not None and flat_http != self.protocol.http:
            raise ValueError("generic.http conflicts with protocol.http")
        if (
            flat_page_size is not None
            and isinstance(type_config, MycoreSolrProtocolConfig)
            and flat_page_size != type_config.page_size
        ):
            raise ValueError(
                f"generic.page_size {flat_page_size!r} conflicts with "
                f"protocol.mycore_solr.page_size {type_config.page_size!r}"
            )
        if flat_page_size is not None and isinstance(type_config, (XmlProtocolConfig, DcatApProtocolConfig)):
            raise ValueError(
                f"generic.page_size is not valid for protocol.{self.protocol.protocol_type.value} (no page_size field)"
            )

    @property
    def effective_protocol(self) -> ProtocolConfig:
        """Nested protocol config after lift (always set post-validation)."""
        if self.protocol is None:
            raise ValueError("generic.protocol is unset; config validation did not run")
        return self.protocol

    @property
    def active_protocol_type(self) -> ProtocolType:
        """Active Protocol type key after lift."""
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
