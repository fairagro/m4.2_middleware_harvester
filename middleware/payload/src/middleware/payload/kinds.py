"""Intermediate payload format discriminators."""

from enum import StrEnum


class PayloadKind(StrEnum):
    """Supported intermediate payload formats.

    Additional kinds may be added later without changing the discriminator
    mechanism.
    """

    rdf_graph = "rdf_graph"
    inspire_record = "inspire_record"
