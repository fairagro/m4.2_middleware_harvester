# Spec Delta

## ADDED Requirements

### Requirement: The Investigation MUST carry the dataset landing page as a Landing Page comment

`GeneralSchemaOrgMapper` MUST add the Investigation comment `Landing Page` with the `schema:url` value, so that
consumers of the ARC can read the landing page under the same key for every RDI. The configured placeholders
(`mapper.placeholders`) apply as for the `URL` comment: an empty or placeholder value MUST NOT produce the comment. The
existing `URL` comment is kept with the same value until the basic-layout export no longer needs it.

#### Scenario: Landing page present

- **WHEN** a Dataset has `schema:url <https://repo.example.org/dataset/abc>`
- **THEN** the Investigation has the comment `Landing Page` = `https://repo.example.org/dataset/abc`
- **AND** the comment `URL` has the same value

#### Scenario: No landing page

- **WHEN** a Dataset has no `schema:url`, or its value matches a configured placeholder
- **THEN** the Investigation has no `Landing Page` comment
