"""Hardened lxml parser for remote XML payloads (MODS, MyCoRe REST lists, …)."""

from __future__ import annotations

import lxml.etree  # type: ignore[import-untyped]

# Same flags as INSPIRE CSW hardening; used explicitly (does not replace the process default).
HARDENED_XML_PARSER = lxml.etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    huge_tree=False,
    remove_comments=True,
)
