"""Intermediate payload format discriminators."""

from enum import StrEnum


class PayloadKind(StrEnum):
    """Supported intermediate payload formats.

    v1 includes ``rdf_graph`` only. Additional kinds may be added later without
    changing the discriminator mechanism.
    """

    rdf_graph = "rdf_graph"
