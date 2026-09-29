"""Import built-in PayloadParser implementations so their ``@…register`` hooks run.

Import this module for its side effects before resolving ``PayloadParser.registry``
(e.g. in harvester config validation or plugin construction).
"""

from __future__ import annotations

from middleware.parsing.parser.html_jsonld import HtmlJsonLdParser
from middleware.parsing.parser.rdf_xml import RdfXmlParser

__all__ = [
    "HtmlJsonLdParser",
    "RdfXmlParser",
]
