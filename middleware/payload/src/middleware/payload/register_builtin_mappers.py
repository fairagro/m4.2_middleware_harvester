"""Import all built-in ``DataMapper`` implementations so their ``@…register`` hooks run.

Import this module for its side effects before resolving ``DataMapper.registry``
(e.g. in harvester config validation or plugin construction).
"""

from __future__ import annotations

from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.linked_data_mapper.ckanext_dcat_mapper import CkanextDcatMapper
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import RegalMapper
from middleware.payload.phenoroam.mapper import PhenoroamMapper

__all__ = [
    "CkanextDcatMapper",
    "GeneralSchemaOrgMapper",
    "InspireMapper",
    "PhenoroamMapper",
    "RegalMapper",
]
