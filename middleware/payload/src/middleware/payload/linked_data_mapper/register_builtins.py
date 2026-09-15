"""Explicit registration of built-in RDF ``DataMapper`` implementations.

Call :func:`register_builtin_mappers` before resolving ``DataMapper.registry``
(e.g. harvester config validation or ``LinkedDataPlugin.create_mapper``).
Importing this package's ``__init__`` alone does **not** load concrete mappers.
"""

from __future__ import annotations


def register_builtin_mappers() -> None:
    """Load Schema.org / Regal mappers so their ``@…register`` decorators run.

    Idempotent: safe to call multiple times (module imports are cached).
    """
    # Intentional deferred imports: concrete mappers pull harvester helpers;
    # keep that edge out of package ``__init__`` and off accidental import paths.
    # pylint: disable=import-outside-toplevel
    from middleware.payload.linked_data_mapper.general_schema_org_mapper import (
        GeneralSchemaOrgMapper,
    )
    from middleware.payload.linked_data_mapper.regal_mapper import RegalMapper

    _ = (GeneralSchemaOrgMapper, RegalMapper)
