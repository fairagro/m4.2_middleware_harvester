## MODIFIED Requirements

### Requirement: The ARC licence MUST come from schema:license

`GeneralSchemaOrgMapper` MUST set `ARC.License` from `schema:license` via `middleware.payload.arc_license`: a
CreativeWork node with `url` gives `name (url)` (or the URL when it has no name); otherwise the URL or text value is the
licence content. The licence MUST keep ARCtrl's default `LICENSE` path; the URL MUST NOT be the licence path or RO-Crate
`@id`. Empty values and placeholders (`middleware.payload.placeholders.is_placeholder`, e.g. an unexpanded
`$licenseURL`) MUST NOT become a licence; without a licence the ARCtrl default "ALL RIGHTS RESERVED BY THE AUTHORS"
stays. Placeholder values MUST NOT become the `License`, `Language`, `Version` or `URL` Investigation Comments or the
Assay `Comment [License]`.

#### Scenario: URL licence

- **WHEN** a Dataset has `schema:license <https://creativecommons.org/licenses/by/4.0/>`
- **THEN** the RO-Crate licence node text MUST be `https://creativecommons.org/licenses/by/4.0/`

#### Scenario: Placeholder licence

- **WHEN** a Dataset has `schema:license "$licenseURL"`
- **THEN** the RO-Crate licence node text MUST be "ALL RIGHTS RESERVED BY THE AUTHORS"
- **AND** the ARC MUST NOT contain `$licenseURL`
