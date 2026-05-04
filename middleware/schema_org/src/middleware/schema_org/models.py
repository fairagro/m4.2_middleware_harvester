"""Schema.org domain models for the Schema.org harvester plugin.

These models represent the subset of Schema.org objects consumed by the
SchemaOrgMapper.

ruff: noqa: A003  # Allow intentional builtin shadowing for property names
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class PostalAddress:
    """Postal address details for a Schema.org contact."""

    street_address: str | None = None
    postal_code: str | None = None
    address_country: str | None = None


@dataclass
class Person:
    """A person referenced by Schema.org metadata."""

    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None
    url: str | None = None
    address: str | PostalAddress | None = None


@dataclass
class Organization:
    """An organization referenced by Schema.org metadata."""

    name: str | None = None
    url: str | None = None
    email: str | None = None
    address: str | PostalAddress | None = None


@dataclass
class DatasetIdentification:
    """Identification and basic metadata for a Schema.org dataset."""

    identifier: str | None = None
    id: str | None = None
    name: str | None = None
    description: str | None = None


@dataclass
class DatasetDates:
    """Date-related metadata for a Schema.org dataset."""

    date_published: str | None = None
    date_modified: str | None = None


@dataclass
class DatasetAgents:
    """Agent-related metadata (creators, authors, contributors, publishers) for a Schema.org dataset."""

    creator: Sequence[Person | Organization] | None = None
    author: Sequence[Person | Organization] | None = None
    contributor: Sequence[Person | Organization] | None = None
    publisher: Organization | None = None


@dataclass
class DatasetMetadata:
    """Descriptive metadata for a Schema.org dataset."""

    citation: str | Sequence[str] | None = None
    keywords: str | Sequence[str] | None = None
    license: str | None = None
    in_language: str | None = None
    version: str | None = None


@dataclass
class DatasetDistribution:
    """Distribution and access metadata for a Schema.org dataset."""

    url: str | None = None
    conforms_to: dict[str, str] | None = None
    distributions: Sequence[dict[str, str]] | None = None


@dataclass
class SchemaOrgDataset:
    """Parsed Schema.org dataset metadata used by the Schema.org mapper.

    This class groups related attributes into logical sub-objects while
    maintaining backward compatibility through properties for direct attribute
    access.
    """

    identification: DatasetIdentification | None = None
    dates: DatasetDates | None = None
    agents: DatasetAgents | None = None
    metadata: DatasetMetadata | None = None
    distribution_info: DatasetDistribution | None = None
