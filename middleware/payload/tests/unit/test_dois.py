"""DOI normalisation (#410)."""

from __future__ import annotations

import pytest

from middleware.payload.dois import normalize_doi


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        ("doi:10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        ("https://doi.org/10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        ("http://dx.doi.org/10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        ("https://www.doi.org/10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        # GeoNode (BonaRes, Thünen Atlas) gmx:Anchor text and href.
        ("doi:https://doi.org/10.4228/zalf.vjcp-vep3", "10.4228/zalf.vjcp-vep3"),
        ("https://dx.doi.org/https://doi.org/10.3220/DATA20230510130443-0", "10.3220/DATA20230510130443-0"),
        ("  DOI: 10.1000.10/x  ", "10.1000.10/x"),
        # Not DOIs.
        ("doi:https://www.ncbi.nlm.nih.gov/search/all/?term=PRJNA1140101", None),
        ("https://dx.doi.org/", None),
        ("978-3-16-148410-0", None),
        ("10.4228", None),
        ("10.abc/x", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_doi(raw: str | None, expected: str | None) -> None:
    assert normalize_doi(raw) == expected
