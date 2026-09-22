"""XML hardening regression tests for the INSPIRE CSW path.

These guard `openspec/specs/csw-xml-hardening/`. lxml parser flags are not introspectable,
so every assertion here is behavioural: parse a hostile document and check what comes out.
"""

from concurrent.futures import ThreadPoolExecutor

import lxml.etree
import pytest

from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.xml_hardening import HARDENED_XML_PARSER

# A local file every CI runner has, used to prove external entities are not resolved.
_XXE_TARGET = "file:///etc/hostname"

_INTERNAL_ENTITY_DOC = b'<!DOCTYPE d [<!ENTITY payload "EXPANDED">]><d>&payload;</d>'
_EXTERNAL_ENTITY_DOC = f'<!DOCTYPE d [<!ENTITY leak SYSTEM "{_XXE_TARGET}">]><d>&leak;</d>'.encode()

_ISO_WITH_COMMENT = b"""<?xml version="1.0"?>
<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd">
  <!-- a comment OWSLib expects to be stripped -->
  <gmd:fileIdentifier>abc-123</gmd:fileIdentifier>
</gmd:MD_Metadata>"""


def _parse_text(payload: bytes) -> str | None:
    """Parse with the installed default parser, returning root text or None on rejection."""
    try:
        return lxml.etree.fromstring(payload).text
    except lxml.etree.XMLSyntaxError:
        return None


def test_inspire_installs_its_own_default_parser() -> None:
    """Hardening is owned here, not inherited from OWSLib's import-time side effect."""
    assert lxml.etree.get_default_parser() is HARDENED_XML_PARSER


def test_internal_entities_are_not_expanded() -> None:
    assert "EXPANDED" not in (_parse_text(_INTERNAL_ENTITY_DOC) or "")


def test_external_entities_do_not_leak_file_contents() -> None:
    """Either rejection or empty text is acceptable; leaking the file is not."""
    with open("/etc/hostname", encoding="utf-8") as handle:  # noqa: PTH123
        secret = handle.read().strip()

    text = _parse_text(_EXTERNAL_ENTITY_DOC) or ""

    assert secret not in text
    assert text == ""


@pytest.mark.parametrize("payload", [_INTERNAL_ENTITY_DOC, _EXTERNAL_ENTITY_DOC])
def test_hardening_applies_on_pool_workers(payload: bytes) -> None:
    """OWSLib calls are parsed on ThreadPoolExecutor workers (see csw-threadpool)."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        text = executor.submit(_parse_text, payload).result() or ""

    assert "EXPANDED" not in text
    assert text == ""


def test_comment_and_namespace_handling_is_unchanged() -> None:
    """The hardened parser must not alter the tree shape OWSLib relies on."""
    root = lxml.etree.fromstring(_ISO_WITH_COMMENT)

    assert root.find("{http://www.isotc211.org/2005/gmd}fileIdentifier").text == "abc-123"
    assert [node for node in root.iter() if isinstance(node, lxml.etree._Comment)] == []


def test_xml_query_template_cannot_expand_entities() -> None:
    """The explicitly-parsed xml_query path is hardened too."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10))
    hostile = (
        '<!DOCTYPE csw:GetRecords [<!ENTITY payload "EXPANDED">]>'
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2">'
        '<csw:Query typeNames="csw:Record">'
        "<csw:ElementSetName>&payload;</csw:ElementSetName>"
        "</csw:Query>"
        "</csw:GetRecords>"
    )

    root, _page_size, _start, _as_bytes = client._prepare_xml_paging(hostile, 10)

    assert "EXPANDED" not in (lxml.etree.tostring(root, encoding="unicode"))


def test_malformed_xml_query_still_raises_value_error() -> None:
    """Hardening must not change the operator-facing error for a broken template."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10))

    with pytest.raises(ValueError, match="not well-formed XML"):
        client._prepare_xml_paging("<csw:GetRecords>", 10)
