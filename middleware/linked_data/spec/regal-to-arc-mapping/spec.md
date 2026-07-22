# Regal-to-ARC Mapping

Transforms a Regal `ResearchData` RDF graph (from inline `/find` JSON-LD) into ARC
investigation components (ISA).

**Authoritative Mapping Source:** [docs/regal_mapping.md](../../../../docs/regal_mapping.md)
defines the conceptual mapping rules. This spec captures the implementation contract.

**Skill Reference:** Agents must load `.agents/skills/arctrl/SKILL.md` when writing or
modifying code that constructs `ArcInvestigation`, `ArcStudy`, or `ArcAssay` objects.

## Requirements

- [ ] Map each Regal `ResearchData` graph to exactly one `ArcInvestigation` with title, description, contacts, publications, and comments as defined in the authoritative mapping source.
- [ ] Create one `ArcStudy` per record containing a Data Collection protocol (when applicable) and a Data Processing protocol.
- [ ] Create a Spatial Sampling protocol on the Study only when `recordingCoordinates` and/or `recordingLocation` are present.
- [ ] Create one `ArcAssay` per record with a single-row annotation table (`Output [URI]`, license/language/`hasPart` comments as specified).
- [ ] Serialize the resulting ARC via `arc.ToROCrateJsonString()` and return the JSON string.
- [ ] Reject (mapping error) graphs that are not Regal ResearchData or that lack both `@id` and `doi`.
- [ ] Implement mapping in a dedicated Regal mapper registered under the Regal `payload_type`; do not reuse `GeneralSchemaOrgMapper`.

## Edge Cases

- Missing title → use `prefLabel` if present; otherwise `"Untitled"`.
- `prefLabel` without `", "` → entire string as `Person.LastName`.
- Empty `hasPart` → omit Online Resource comment columns.
- Duplicate funder information in flat and `joinedFunding` fields → prefer `joinedFunding`.
