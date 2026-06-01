# EDAL-PGP Mapping

Map EDAL-PGP schema.org JSON-LD datasets to ARC RO-Crate objects.

## Requirements

- Register mapper for `PayloadType.edal_pgp`.
- Detect and handle the literal placeholder `"$licenseURL"` in the `license` field. When encountered, emit a `Comment("License", "URL not provided")` instead of the placeholder value.
- Parse non-ISO `datePublished` format `"<dow> <mon> <dd> <time> <tz> <yyyy>"` (e.g. `"Sat Jan 01 00:00:00 CET 2011"`) and output ISO 8601 `YYYY-MM-DD`.
- Deduplicate persons across `creator`, `author`, and `contributor` arrays using ORCID as primary key and `(givenName, familyName)` as secondary key. The richer record (with ORCID, structured address) survives.
- Extract ORCID from the nested `identifier` PropertyValue structure and store as `Person.Comments[("ORCID", …)]`.
- Handle two address formats on `Person`: structured `PostalAddress` object and plain string literal. For plain strings, parse by splitting on comma.
- When `schema:keywords` is a single comma-separated string, split into individual terms.
- Fall back to `http://purl.org/dc/terms/conformsTo` when `schema:conformsTo` is not present on the dataset.
- Truncate `ArcStudy.description` to 500 characters when the source `description` exceeds that length.

## Inheritance

`EdalPgpMapper(GeneralSchemaOrgMapper)` — inherits all general mapping logic, overrides the diverging methods documented in `design.md`. The general mapper's logic for Investigation/Study/Assay assembly, table construction, ontology sources, and RO-Crate serialization is reused unchanged.

## Edge Cases

| Case | Behavior |
|------|----------|
| `$licenseURL` placeholder | Emit `Comment("License", "URL not provided")` — do not propagate the literal placeholder |
| Non-ISO `datePublished` | Parse and re-emit as `YYYY-MM-DD` |
| Person appears in both `creator` and `author` | Dedup by ORCID → keep the richer record; if no ORCID, dedup by `(given, family)` |
| Person `address` is a plain string | Parse by splitting on commas: first part = street, second = postal code, third = country |
| ORCID nested under `Person.identifier(PropertyValue)` | Extract via `identifier.propertyID == "orcid"` → `Person.Comments` |
| `keywords` is a string (not an array) | Split on `,`, trim whitespace, rejoin |
| No `schema:conformsTo` present | Fall back to `dcterms:conformsTo` (`http://purl.org/dc/terms/conformsTo`) |
| Long description (>500 chars) in study | Investigation gets full text; Study gets truncated to 500 chars |
