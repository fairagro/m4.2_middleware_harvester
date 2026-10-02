## Why

The Publisso context maps `contributorOrder` to `http://purl.org/lobid/lv#contributorOrder`, but the mapper, spec, docs
and tests only knew `regal:contributorOrder`. Today the value arrives as an `@list` whose head has no text, so it is
dropped by chance; a plain literal (`"https://orcid.org/… | …"`) would leak out as an opaque `contributorOrder` Comment.

Tracked as GitHub [#419](https://github.com/fairagro/m4.2_middleware_harvester/issues/419).

## What Changes

- `LV` namespace; `lv:contributorOrder` is a known predicate (kept next to `regal:contributorOrder`).
- Drop the "sort Contacts by contributorOrder" TODO: in all 28 live records carrying it, it equals the creator list (15)
  or creators + contributors (13), the Contact order #418 already produces.
- Spec, design note and docs name the real predicate; tests cover the literal case and the real `frl:6420709` payload.

## Capabilities

### Modified Capabilities

- `regal-to-arc-mapping`: contributorOrder requirement names `lv:contributorOrder` and states it is not used for
  sorting.

## Impact

- No change in published ARCs for current Publisso data.
