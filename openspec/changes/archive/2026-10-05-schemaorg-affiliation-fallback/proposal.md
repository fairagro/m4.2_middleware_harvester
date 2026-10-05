## Why

e!DAL gives no `schema:affiliation` and puts the institute at the start of a flat `address` string ("Leibniz Institute
of Plant Genetics and Crop Plant Research (IPK), Seeland OT Gatersleben, Corrensstraße 3, D-06466, Germany").
`Person.Address` is not exported to the hub layout, so the affiliation was empty for every e!DAL person (live
2026-10-05: 1,787 persons in 292 records, none with an affiliation). Tracked as GitHub
[#414](https://github.com/fairagro/m4.2_middleware_harvester/issues/414). The flat string may be an e!DAL workaround for
our earlier lack of structured-address support, so e!DAL will be asked for a structured address again; the mapper has to
handle both shapes.

## What Changes

- `GeneralSchemaOrgMapper`: when a Person has no `affiliation` and `address` is a plain string, the first non-empty
  comma-separated segment becomes `Person.Affiliation`. The full address is kept.
- A plain-string address made only of commas and whitespace (e!DAL renders empty addresses as `" ,  , "`) is absent.
- A structured `PostalAddress` now also keeps `addressLocality` and `addressRegion`
  (`streetAddress, postalCode, addressLocality, addressRegion, addressCountry`). It gives no affiliation.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: Person affiliation fallback and address flattening.

## Impact

- Live e!DAL (338 ARCs): 1,778 of 1,787 persons now have an affiliation (all 292 records with persons); 9 comma-only
  addresses are dropped. No other ARC change.
