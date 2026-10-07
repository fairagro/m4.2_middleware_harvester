## MODIFIED Requirements

### Requirement: The ARC licence MUST come from schema:license

`GeneralSchemaOrgMapper` MUST set `ARC.License` from `schema:license` via `middleware.payload.arc_license`: a
CreativeWork node with `url` gives `name (url)` (or the URL when it has no name); otherwise the URL or text value is the
licence content. The licence MUST keep ARCtrl's default `LICENSE` path; the URL MUST NOT be the licence path or RO-Crate
`@id`. Empty values and the repository's configured placeholders (`mapper.placeholders`: `values`, and unrendered
templates such as `$licenseURL` when `unrendered_templates` is set) MUST NOT become a licence; without a licence the
ARCtrl default "ALL RIGHTS RESERVED BY THE AUTHORS" stays. Placeholder values MUST NOT become the `License`, `Language`,
`Version` or `URL` Investigation Comments or the Assay `Comment [License]`. `RegalMapper` MUST apply the same
placeholders to its ARC licence. Without configured placeholders, every non-empty value MUST be kept.

#### Scenario: URL licence

- **WHEN** a Dataset has `schema:license <https://creativecommons.org/licenses/by/4.0/>`
- **THEN** the RO-Crate licence node text MUST be `https://creativecommons.org/licenses/by/4.0/`

#### Scenario: Placeholder licence

- **WHEN** the repository sets `mapper.placeholders.unrendered_templates: true`
- **AND** a Dataset has `schema:license "$licenseURL"`
- **THEN** the RO-Crate licence node text MUST be "ALL RIGHTS RESERVED BY THE AUTHORS"
- **AND** the ARC MUST NOT contain `$licenseURL`

#### Scenario: Per-RDI placeholder

- **WHEN** the repository's `mapper.placeholders.values` is ["Lizenz folgt"] and a Dataset has
  `schema:license "Lizenz folgt"` and `schema:version "None"`
- **THEN** the ARC MUST NOT contain "Lizenz folgt" and MUST keep the `Version` Comment "None"
