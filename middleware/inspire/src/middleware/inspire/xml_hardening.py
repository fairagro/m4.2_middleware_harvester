"""Explicit lxml parser hardening for the INSPIRE CSW path.

OWSLib parses every CSW response internally and exposes no parser argument, so lxml's
process default parser is the only lever over it. OWSLib already installs a default at
import time (`owslib/etree.py`: ``XMLParser(resolve_entities=False, remove_comments=True)``),
which means entity expansion is disabled today only as a third-party side effect on global
mutable state — undocumented, untested, and lost if OWSLib ever drops it.

This module replaces that incidental guarantee with an explicit one. Importing ``owslib.etree``
first, here, means our ``set_default_parser`` call always runs afterwards and wins, regardless
of the order in which other modules are imported.

Worker threads inherit a copy of the main thread's default parser when they are created, so
this also covers the bounded pool used for OWSLib calls (``openspec/specs/csw-threadpool/``).
The parser object is created once and never mutated, so there is no cross-thread write.

See ``openspec/specs/csw-xml-hardening/``.
"""

import lxml.etree  # type: ignore[import-untyped]
import owslib.etree  # type: ignore[import-untyped]  # noqa: F401  # imported for its default-parser side effect

# No entity expansion, no DTD loading, no network retrieval, bounded tree size.
# `remove_comments=True` mirrors OWSLib's own parser so tree shape is unchanged.
HARDENED_XML_PARSER = lxml.etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    huge_tree=False,
    remove_comments=True,
)

lxml.etree.set_default_parser(HARDENED_XML_PARSER)
