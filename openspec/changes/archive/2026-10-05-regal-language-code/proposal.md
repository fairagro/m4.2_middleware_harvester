## Why

Regal (Publisso) gives `language` as `{"prefLabel": "Englisch", "@id": "http://id.loc.gov/vocabulary/iso639-2/eng"}`.
`RegalMapper` wrote the joined `prefLabel` values into the `Language` comments, so the DataHUB shows a German display
label ("Englisch" 89, "English" 3 of 92 Publisso records) instead of a language code. Tracked as GitHub
[#412](https://github.com/fairagro/m4.2_middleware_harvester/issues/412).

## What Changes

- `RegalMapper` derives the ISO 639 code from `id.loc.gov/vocabulary/iso639-1|2/<code>` language IRIs (lower case) and
  uses the `prefLabel` only when there is no such IRI. Values are deduplicated and joined with `; `. This applies to
  both the Investigation `Language` comment and the Assay `Comment [Language]` column.

## Capabilities

### Modified Capabilities

- `regal-to-arc-mapping`: language code.

## Impact

- All 92 live Publisso records have the `iso639-2/eng` IRI and now carry `eng`. Other mappers are unchanged.
