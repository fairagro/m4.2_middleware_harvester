# Proposal

## Why

#485: the Search Hub review of the DWD dump found no harmonised licence. DWD records (harvested from the GDI-DE
catalogue) state the licence as GDI-DE JSON in `gmd:otherConstraints`, e.g.
`{"id": "cc-by/4.0", "name": "Creative Commons Namensnennung – 4.0 International (CC BY 4.0)", "url": "https://creativecommons.org/licenses/by/4.0/", "quelle": "…"}`.
`inspire_license` matched that text only through the licence-host rule, so the whole JSON blob became the licence text.
A live DWD harvest on 2026-10-14 found 15 of 82 records like this, 4 of them with invalid JSON (`"name\": …`).

## What Changes

- `inspire_license` reads a GDI-DE JSON constraint before the GeoNode and free-text rules. The licence is `name (url)`,
  or the URL alone without a name. Without an http(s) `url` the constraint gives no licence.
- Malformed JSON is read field by field (`name`, `url`), since DWD publishes it that way.
- **Non-goals:** GeoNutzV free text without JSON (8 DWD records keep the ARCtrl default); licence parsing for other
  mappers.

## Capabilities

### Modified Capabilities

- `inspire-to-arc-mapping`: licence order gains the GDI-DE JSON licence.

## Impact

- `middleware/payload/src/middleware/payload/arc_license.py`, `middleware/payload/tests/unit/test_arc_license.py`
- `docs/mappers/inspire.md`
