"""Unit tests for the Protocol registry (parsers are tested in middleware.parsing)."""

from __future__ import annotations

import middleware.generic.protocol.xml as _register_xml
from middleware.generic.config import ProtocolType
from middleware.generic.protocol.protocol import Protocol

_ = _register_xml


def test_xml_protocol_registered() -> None:
    assert ProtocolType.xml in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.xml], Protocol)
