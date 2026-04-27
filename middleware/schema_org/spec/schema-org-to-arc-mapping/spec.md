# Schema.org to ARC Mapping

## Requirements

- [ ] Map Schema.org `Dataset` objects to ARC Investigation/Study/Assay structure
- [ ] Extract and map the following Schema.org properties:
  - [ ] `@id` / `identifier` → ARC Investigation identifier
  - [ ] `name` → ARC title
  - [ ] `description` → ARC description
  - [ ] `datePublished` → ARC submission date
  - [ ] `creator` / `author` → ARC Contacts (with author role)
  - [ ] `contributor` → ARC Contacts (with contributor role)
  - [ ] `publisher` → ARC Contacts (with publisher role)
  - [ ] `keywords` → ARC Comments
  - [ ] `license` → ARC Comments
  - [ ] `url` → ARC Comments / Output URI
- [ ] Handle Schema.org Person and Organization types for contacts
- [ ] Handle nested PostalAddress objects
- [ ] Extract DOI from identifier fields for Publication mapping
- [ ] Create minimal Study and Assay protocols for data processing context
- [ ] Add Schema.org ontology source reference

## Schema.org Profile Support

The mapper supports datasets conforming to:

- Schema.org Dataset (generic)
- BioSchemas Dataset profile
- EDAL, BONARES, OpenAgris, Publisso, Thünen Atlas provider extensions

## Output Structure

Each Schema.org Dataset is converted to an ARC with:

- **1 Investigation**: Contains metadata, contacts, publications
- **1 Study**: Contains data collection and processing protocols
- **1 Assay**: Contains measurement annotation table with output URI
