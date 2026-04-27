"""Pydantic models for Schema.org metadata structures."""

from pydantic import BaseModel, ConfigDict, Field


class PostalAddress(BaseModel):
    """Schema.org PostalAddress model."""

    model_config = ConfigDict(populate_by_name=True)

    street_address: str | None = Field(None, alias="streetAddress")
    postal_code: str | None = Field(None, alias="postalCode")
    address_country: str | None = Field(None, alias="addressCountry")
    address_locality: str | None = Field(None, alias="addressLocality")
    address_region: str | None = Field(None, alias="addressRegion")


class Person(BaseModel):
    """Schema.org Person model."""

    model_config = ConfigDict(populate_by_name=True)

    given_name: str | None = Field(None, alias="givenName")
    family_name: str | None = Field(None, alias="familyName")
    name: str | None = None
    email: str | None = None
    url: str | None = None
    address: PostalAddress | str | None = None


class Organization(BaseModel):
    """Schema.org Organization model."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    url: str | None = None
    address: PostalAddress | str | None = None


class SchemaOrgDataset(BaseModel):
    """Schema.org Dataset model for metadata records."""

    model_config = ConfigDict(populate_by_name=True)

    context: str | None = Field(None, alias="@context")
    id: str | None = Field(None, alias="@id")
    type: str | list[str] | None = Field(None, alias="@type")
    name: str | None = None
    description: str | None = None
    url: str | None = None
    identifier: str | dict | None = None
    date_published: str | None = Field(None, alias="datePublished")
    date_modified: str | None = Field(None, alias="dateModified")
    creator: list[Person] | list[Organization] | None = None
    author: list[Person] | list[Organization] | None = None
    contributor: list[Person] | list[Organization] | None = None
    publisher: Organization | None = None
    keywords: str | list[str] | None = None
    license: str | dict | None = None
    distribution: list[dict] | None = None
    included_in_data_catalog: dict | None = Field(None, alias="includedInDataCatalog")
    conforms_to: dict | None = Field(None, alias="conformsTo")
    in_language: str | None = Field(None, alias="inLanguage")
    version: str | None = None
    citation: str | list[str] | None = None
    is_part_of: dict | None = Field(None, alias="isPartOf")
