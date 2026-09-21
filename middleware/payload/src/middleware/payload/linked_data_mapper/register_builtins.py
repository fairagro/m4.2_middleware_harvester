"""Import built-in RDF ``DataMapper`` implementations so their ``@…register`` hooks run.

Import this module for its side effects before resolving ``DataMapper.registry``
(e.g. in harvester config validation or ``LinkedDataPlugin.create_mapper``).
"""

from __future__ import annotations

from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import RegalMapper

__all__ = [
    "GeneralSchemaOrgMapper",
    "RegalMapper",
]
