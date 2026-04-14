# INSPIRE-to-ARC Mapping

Transforms the fully populated `InspireRecord` object into ARC investigation components (ISA).

**Authoritative Mapping Source:** The definitive source for the conceptual mapping rules is [docs/inspire_to_arc_mapping.md](../../../../docs/inspire_to_arc_mapping.md).

**Skill Reference:** Agents must load and follow `.agents/skills/arctrl/SKILL.md` when writing or modifying the code that constructs the `ArcInvestigation`, `ArcStudy`, and `ArcAssay` objects.

## Requirements

- [ ] Execute the mapping logic exactly as defined in the authoritative mapping source document.
- [ ] Use the `arctrl` Python library to systematically build ARC ISA objects.
- [ ] Final output: Generate an `arctrl` compliant ARC object packing the generated Investigation, Study, Assay alongside the raw ISO xml representation.
