## ADDED Requirements

### Requirement: The ARC licence MUST come from gmd:otherConstraints

`InspireMapper` MUST set `ARC.License` via `middleware.payload.arc_license.inspire_license`, keeping ARCtrl's default
`LICENSE` path. The licence content MUST be, in order: the first `gmx:Anchor/@xlink:href` that is not an
`inspire.ec.europa.eu` code-list URI; the first GeoNode licence text `Name (id): description`; the first text that
contains a URL on a known licence host. A GeoNode `Not Specified` entry, access notes and other free text MUST NOT
become a licence; then the ARCtrl default "ALL RIGHTS RESERVED BY THE AUTHORS" stays.

#### Scenario: GeoNode licence text

- **WHEN** `otherConstraints` is `CC-BY (CC-BY): https://creativecommons.org/licenses/by/4.0/ (…/legalcode)` followed by
  a disclaimer
- **THEN** the RO-Crate licence node text MUST be the `CC-BY (CC-BY): …` constraint

#### Scenario: No licence specified

- **WHEN** `otherConstraints` is `Not Specified: The original author did not specify a license.`
- **THEN** the RO-Crate licence node text MUST be "ALL RIGHTS RESERVED BY THE AUTHORS"

#### Scenario: Written ARC keeps the licence as a file

- **WHEN** the RO-Crate is read with `ARC.from_rocrate_json_string` and written with `ARC.Write`
- **THEN** the ARC MUST contain a `LICENSE` file with the licence text and no directory named after a URL
