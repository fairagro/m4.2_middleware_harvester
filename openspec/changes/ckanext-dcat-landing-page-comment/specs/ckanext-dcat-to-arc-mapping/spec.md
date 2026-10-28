# Spec Delta

## ADDED Requirements

### Requirement: The Investigation MUST carry the dataset landing page as a Landing Page comment

The `ckanext_dcat` mapper MUST add exactly one Investigation comment `Landing Page` when a landing page is known, so
that ARC consumers read it under the same key as for the schema.org and Regal mappers. The value MUST be the first
http(s) `dcat:landingPage` in a deterministic order; when there is none, it MUST be the `dcat:Dataset` IRI if that IRI
is http(s). Otherwise the mapper MUST add no `Landing Page` comment and mapping MUST still succeed. The mapper MUST NOT
add a `URL` comment.

#### Scenario: Explicit landing page

- **GIVEN** a `dcat:Dataset` with `dcat:landingPage` `https://repo.example.org/page/abc`
- **WHEN** it is mapped
- **THEN** the Investigation has the comment `Landing Page` = `https://repo.example.org/page/abc`

#### Scenario: Dataset IRI as landing page

- **GIVEN** a `dcat:Dataset` with IRI `https://ckan.example.org/dataset/abc` and no `dcat:landingPage`
- **WHEN** it is mapped
- **THEN** the Investigation has the comment `Landing Page` = `https://ckan.example.org/dataset/abc`

#### Scenario: Several landing pages

- **GIVEN** a `dcat:Dataset` with two http(s) `dcat:landingPage` values
- **WHEN** it is mapped twice
- **THEN** the Investigation has exactly one `Landing Page` comment, with the same value both times

#### Scenario: No usable landing page

- **GIVEN** a `dcat:Dataset` whose IRI is not http(s) (for example `urn:uuid:…`) and that has no http(s) `dcat:landingPage`
- **WHEN** it is mapped
- **THEN** the Investigation has no `Landing Page` comment and mapping succeeds

#### Scenario: No URL comment

- **WHEN** any `dcat:Dataset` is mapped
- **THEN** the Investigation has no `URL` comment
