# Spec Delta

## ADDED Requirements

### Requirement: The Investigation MUST carry the record landing page as a Landing Page comment

`RegalMapper` MUST add the Investigation comment `Landing Page` = `{resource_base_url}{@id}` (the same expansion it
already uses for the Assay `Output [URI]` fallback). The Assay `Output [URI]` column is not affected by this
requirement.

#### Scenario: Landing page from the record id

- **WHEN** a Regal record with `@id` `frl:6420709` is mapped and `resource_base_url` is
  `https://repository.publisso.de/resource/`
- **THEN** the Investigation has the comment `Landing Page` = `https://repository.publisso.de/resource/frl:6420709`

#### Scenario: Assay output unchanged

- **WHEN** any record is mapped
- **THEN** the Assay annotation table's `Output [URI]` column has the same value as before this change
