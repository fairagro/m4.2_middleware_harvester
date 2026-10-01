"""Unit tests for the Protocol registry (parsers are tested in middleware.parsing)."""

from __future__ import annotations

import middleware.generic.protocol.regal_find as _register_regal_find
import middleware.generic.protocol.static_json_array as _register_static_json_array
import middleware.generic.protocol.xml as _register_xml
from middleware.generic.config import ProtocolType
from middleware.generic.protocol.json_array import JsonArrayProtocol
from middleware.generic.protocol.protocol import Protocol

_ = (_register_xml, _register_static_json_array, _register_regal_find)


def test_xml_protocol_registered() -> None:
    assert ProtocolType.xml in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.xml], Protocol)


def test_json_array_protocols_share_base() -> None:
    for protocol_type in (ProtocolType.static_json_array, ProtocolType.regal_find):
        assert issubclass(Protocol.registry[protocol_type], JsonArrayProtocol)
