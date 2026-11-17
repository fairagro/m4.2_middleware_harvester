# Design

## Context

See `proposal.md` — Why. Schema.org and Regal already set `Person.ORCID` via `orcid_id` (#405 / Regal mapping). INSPIRE
still puts contact `CI_OnlineResource` on Person Comments (docs say “ORCID or website”). MODS already passes
`Person.create(orcid=…)` but only after `.strip()`, not `orcid_id` normalization. Shared helper:
`middleware.payload.person_contacts.orcid_id`.

## Goals / Non-Goals

**Goals:**

- One ORCID policy for Person-emitting mappers in this slice: field first (B1), bare iD, shared `orcid_id`.
- INSPIRE + MODS behaviour + docs + unit tests aligned with Schema.org/Regal.

**Non-Goals:**

- PhenoRoam / ckanext-dcat Person ORCID (no source ORCID / no Person creators today).
- Switching INSPIRE contacts to `add_contact` merge semantics (out of scope unless needed for ORCID).
- Changing Schema.org/Regal contracts that already satisfy the field.

## Decisions

1. **INSPIRE: detect ORCID on `online_resource_url`, fallback `online_resource_name`** ISO often puts the ORCID URL in
   `linkage` (`online_resource_url`); some catalogues put a bare iD or labelled name in `name`. Prefer URL; if URL is
   absent/non-ORCID, try name. Rationale: matches docs “ORCID or website” without inventing new Contact model fields.
   Alternative rejected: only URL — would miss bare-iD-only catalogues.

2. **B1: no duplicate ORCID Comment when `Person.ORCID` is set** Same as Regal/Schema.org. Non-ORCID websites keep
   Comments. Alternative rejected: keep Comment for “compat” — Search Hub / #551 need the field; duplicate Comments
   confuse consumers.

3. **MODS: wrap existing orcid string with `orcid_id`** Parser already selects `type=orcid`; mapper normalizes.
   Alternative rejected: parse-time normalize only — mapper is the ARC boundary and matches Schema.org/Regal.

4. **PhenoRoam / ckanext: document-only non-goals** No speculative model fields. Follow-up issues if sources gain ORCID
   / Person agents.

## Risks / Trade-offs

- [INSPIRE onlineResource name used for non-ORCID labels] → Only promote when `orcid_id` succeeds; otherwise Comment.
- [Catalogues encode ORCID only in free-text positionName] → Out of scope; would need fuzzy parse (deferred).
- [Existing fixtures expect ORCID Comment] → Update tests/docs with the field behaviour.

## Migration Plan

Ship with the usual harvester image; no config flag. Re-harvest updates Persons. Rollback = revert mapper commits.
