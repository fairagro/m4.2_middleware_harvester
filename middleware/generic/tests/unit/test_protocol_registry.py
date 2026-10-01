"""Unit tests for the Protocol registry (parsers are tested in middleware.parsing)."""

from __future__ import annotations

import middleware.generic.protocol.dcat_ap as _register_dcat_ap
import middleware.generic.protocol.mycore_solr as _register_mycore_solr
import middleware.generic.protocol.xml as _register_xml
from middleware.generic.protocol.protocol import Protocol, ProtocolType

_ = (_register_xml, _register_mycore_solr, _register_dcat_ap)


def test_xml_protocol_registered() -> None:
    assert ProtocolType.xml in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.xml], Protocol)


def test_mycore_solr_protocol_registered() -> None:
    assert ProtocolType.mycore_solr in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.mycore_solr], Protocol)


def test_dcat_ap_protocol_registered() -> None:
    assert ProtocolType.dcat_ap in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.dcat_ap], Protocol)
