"""Typed intermediate models for PhenoRoam ``pr:metadataDataset`` records."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PhenoroamPerson(BaseModel):
    """Contact person from ``pr:blockPerson``."""

    name: str | None = None
    email: str | None = None
    affiliation: str | None = None


class PhenoroamStudyBlock(BaseModel):
    """Nested study / investigation titles from ``pr:blockStudyParent``."""

    study_title: str | None = None
    study_description: str | None = None
    investigation_title: str | None = None
    investigation_description: str | None = None


class PhenoroamBBox(BaseModel):
    """Geographic bounding box from ``pr:blockBBox``."""

    west: str | None = None
    east: str | None = None
    south: str | None = None
    north: str | None = None


class PhenoroamRecord(BaseModel):
    """Parsed PhenoRoam metadata dataset ready for ARC mapping."""

    item_uuid: str | None = None
    title: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    responsible_contacts: list[PhenoroamPerson] = Field(default_factory=list)
    other_contacts: list[PhenoroamPerson] = Field(default_factory=list)
    study: PhenoroamStudyBlock | None = None
    datafile_links: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    license_text: str | None = None
    how_to_cite: str | None = None
    funded_by: str | None = None
    download_information: str | None = None
    core_projects: list[str] = Field(default_factory=list)
    bbox: PhenoroamBBox | None = None
    md_change_date: str | None = None
