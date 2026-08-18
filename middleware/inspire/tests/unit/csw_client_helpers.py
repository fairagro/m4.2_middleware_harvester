"""Shared helpers for INSPIRE CSW client unit tests."""

from middleware.inspire.config import Config
from middleware.inspire.models import InspireRecord

_expected_record_count = 42


def _make_csw_config(csw_url: str = "https://example.com/csw") -> Config:
    return Config(csw_url=csw_url, timeout=5, chunk_size=10)


def _minimal_get_records_xml(**attrs: str) -> str:
    attr_str = " ".join(f'{key}="{value}"' for key, value in attrs.items())
    return (
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2" resultType="results" '
        'outputSchema="http://www.isotc211.org/2005/gmd"'
        f"{(' ' + attr_str) if attr_str else ''}>"
        '<csw:Query typeNames="csw:Record">'
        "<csw:ElementSetName>full</csw:ElementSetName>"
        "</csw:Query>"
        "</csw:GetRecords>"
    )


def _stub_inspire_record(identifier: str) -> InspireRecord:
    """Minimal InspireRecord for limit/pagination unit tests."""
    return InspireRecord.model_construct(identifier=identifier, title=identifier, abstract="")
