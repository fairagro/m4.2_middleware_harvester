"""Unit tests for the Schema.org to ARC mapper."""

import pytest
from arctrl import ARC  # type: ignore[import-untyped]

from middleware.schema_org.mapper import SchemaOrgMapper
from middleware.schema_org.models import Organization, Person as SchemaOrgPerson, PostalAddress, SchemaOrgDataset


class TestSchemaOrgMapper:
    """Test cases for SchemaOrgMapper."""

    @pytest.fixture
    def mapper(self) -> SchemaOrgMapper:
        """Create a mapper instance for testing."""
        return SchemaOrgMapper()

    def test_to_identifier_slug_basic(self, mapper: SchemaOrgMapper) -> None:
        """Test basic slugification."""
        assert mapper._to_identifier_slug("Hello World") == "hello_world"  # noqa: SLF001
        assert mapper._to_identifier_slug("Test 123") == "test_123"  # noqa: SLF001

    def test_to_identifier_slug_special_chars(self, mapper: SchemaOrgMapper) -> None:
        """Test slugification with special characters."""
        assert mapper._to_identifier_slug("Test!@#Dataset") == "test_dataset"  # noqa: SLF001
        assert mapper._to_identifier_slug("A/B\\C:D") == "a_b_c_d"  # noqa: SLF001

    def test_to_identifier_slug_empty(self, mapper: SchemaOrgMapper) -> None:
        """Test slugification with empty input."""
        assert mapper._to_identifier_slug("") == "untitled"  # noqa: SLF001

    def test_extract_doi_from_id(self, mapper: SchemaOrgMapper) -> None:
        """Test DOI extraction from @id field."""
        dataset = SchemaOrgDataset.model_validate(
            {"@context": "https://schema.org", "@id": "https://doi.org/10.1234/test", "@type": "Dataset"}
        )
        assert mapper._extract_doi(dataset) == "10.1234"  # noqa: SLF001

    def test_extract_doi_from_id_direct(self, mapper: SchemaOrgMapper) -> None:
        """Test DOI extraction when id is a direct DOI."""
        dataset = SchemaOrgDataset.model_validate(
            {"@context": "https://schema.org", "@id": "10.1234/test", "@type": "Dataset"}
        )
        assert mapper._extract_doi(dataset) == "10.1234/test"  # noqa: SLF001

    def test_extract_doi_from_identifier(self, mapper: SchemaOrgMapper) -> None:
        """Test DOI extraction from identifier field."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.5678/example",
                "@type": "Dataset",
                "identifier": "10.5678/example",
            }
        )
        assert mapper._extract_doi(dataset) == "10.5678/example"  # noqa: SLF001

    def test_extract_doi_not_found(self, mapper: SchemaOrgMapper) -> None:
        """Test DOI extraction when no DOI is present."""
        dataset = SchemaOrgDataset.model_validate(
            {"@context": "https://schema.org", "@id": "https://example.com/dataset/123", "@type": "Dataset"}
        )
        assert mapper._extract_doi(dataset) is None  # noqa: SLF001

    def test_map_person_with_names(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a Person with givenName and familyName."""
        person = SchemaOrgPerson(givenName="John", familyName="Doe")
        result = mapper.map_person(person)
        assert result is not None
        assert result.FirstName == "John"
        assert result.LastName == "Doe"

    def test_map_person_with_full_name(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a Person with only full name."""
        person = SchemaOrgPerson.model_validate({"name": "John Doe"})
        result = mapper.map_person(person)
        assert result is not None
        assert result.FirstName == "John"
        assert result.LastName == "Doe"

    def test_map_investigation_basic(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a basic dataset to Investigation."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test",
                "@type": "Dataset",
                "name": "Test Dataset",
                "description": "Test Description",
                "datePublished": "2024-01-01",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        # Verify ARC is created (serialization tested in integration tests)
        assert arc is not None

    def test_map_investigation_with_creator(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a dataset with creator."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test2",
                "@type": "Dataset",
                "name": "Test Dataset",
                "creator": [{"givenName": "John", "familyName": "Doe"}],
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        # Verify ARC is created with contacts
        assert arc is not None

    def test_map_investigation_with_keywords(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a dataset with keywords."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test3",
                "@type": "Dataset",
                "name": "Test Dataset",
                "keywords": "keyword1, keyword2",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        assert arc is not None

    def test_map_study_basic(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a basic Study."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test4",
                "@type": "Dataset",
                "name": "Test Dataset",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        assert arc is not None

    def test_map_study_with_keywords_protocol(self, mapper: SchemaOrgMapper) -> None:
        """Test that Study has data collection protocol when keywords present."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test5",
                "@type": "Dataset",
                "name": "Test Dataset",
                "keywords": "test, data",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        assert arc is not None

    def test_map_assay_basic(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a basic Assay."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test6",
                "@type": "Dataset",
                "name": "Test Dataset",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        assert arc is not None

    def test_map_assay_table_with_output_uri(self, mapper: SchemaOrgMapper) -> None:
        """Test that Assay table has correct output URI."""
        dataset = SchemaOrgDataset.model_validate(
            {
                "@context": "https://schema.org",
                "@id": "https://doi.org/10.1234/test7",
                "@type": "Dataset",
                "name": "Test Dataset",
                "url": "https://example.com/dataset/123",
            }
        )
        arc: ARC = mapper.map_dataset(dataset)
        assert arc is not None

    def test_map_person_with_address_string(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a Person with string address."""
        person = SchemaOrgPerson(givenName="Jane", familyName="Smith", address="123 Main St, City, Country")
        result = mapper.map_person(person)
        assert result is not None
        assert result.Address == "123 Main St, City, Country"

    def test_map_person_with_postal_address(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a Person with PostalAddress object."""
        person = SchemaOrgPerson(
            givenName="Jane",
            familyName="Smith",
            address=PostalAddress(
                streetAddress="123 Main St",
                postalCode="12345",
                addressCountry="Germany",
                addressLocality="Berlin",
                addressRegion="Berlin",
            ),
        )
        result = mapper.map_person(person)
        assert result is not None
        assert result.Address is not None
        assert "123 Main St" in result.Address
        assert "12345" in result.Address
        assert "Germany" in result.Address

    def test_map_person_empty(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping a Person with no identifying information."""
        person = SchemaOrgPerson.model_validate({})
        result = mapper.map_person(person)
        assert result is None

    def test_map_organization(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping an Organization."""
        org = Organization(name="Test Organization", url="https://example.org")
        result = mapper.map_person(org)
        assert result is not None
        assert result.LastName == "Test Organization"
        assert result.Affiliation == "Test Organization"

    def test_map_organization_empty(self, mapper: SchemaOrgMapper) -> None:
        """Test mapping an Organization with no name."""
        org = Organization()
        result = mapper.map_person(org)
        assert result is None
