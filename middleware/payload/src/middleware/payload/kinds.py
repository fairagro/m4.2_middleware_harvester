"""Intermediate payload format discriminators."""

from enum import StrEnum


class PayloadKind(StrEnum):
    """Supported intermediate payload formats.

    Additional kinds may be added without changing the discriminator mechanism.
    """

    rdf_graph = "rdf_graph"
    phenoroam_record = "phenoroam_record"
