"""Typed intermediate models for MODS records extracted from MyCoRe object XML."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModsName(BaseModel):
    """Personal or corporate name from ``mods:name``."""

    display_form: str | None = None
    given: str | None = None
    family: str | None = None
    affiliation: str | None = None
    orcid: str | None = None
    gnd: str | None = None
    role_codes: list[str] = Field(default_factory=list)
    name_type: str | None = None


class ModsRecord(BaseModel):
    """Parsed MODS metadata ready for ARC mapping."""

    object_id: str | None = None
    title: str | None = None
    abstract: str | None = None
    doi: str | None = None
    date_issued: str | None = None
    license_uri: str | None = None
    license_label: str | None = None
    language: str | None = None
    names: list[ModsName] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    datafile_names: list[str] = Field(default_factory=list)
