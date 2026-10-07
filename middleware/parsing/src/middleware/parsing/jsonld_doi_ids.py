"""Bare-DOI JSON-LD ``@id`` values as ``https://doi.org/`` IRIs.

e!DAL writes the Dataset ``@id`` as a bare DOI (``10.5447/ipk/2011/0``). JSON-LD reads that
as a relative IRI, and rdflib resolves it against the process working directory
(``file:///app/10.5447/ipk/2011/0``), so the dataset's own DOI never reached the ARC (#416).
A bare DOI is never meant as a relative path, so it is rewritten before parsing.
"""

from __future__ import annotations

from typing import Any

from middleware.payload.dois import normalize_doi


def doi_ids_as_iris(value: Any) -> Any:
    """Return ``value`` with every ``@id`` that is a bare DOI turned into ``https://doi.org/<doi>``."""
    if isinstance(value, list):
        return [doi_ids_as_iris(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: doi_ids_as_iris(item) for key, item in value.items()}
    node_id = value.get("@id")
    if isinstance(node_id, str) and node_id.strip().startswith("10."):
        doi = normalize_doi(node_id)
        if doi:
            result["@id"] = f"https://doi.org/{doi}"
    return result
