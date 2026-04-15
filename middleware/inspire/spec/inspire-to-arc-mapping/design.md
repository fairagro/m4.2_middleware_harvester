# INSPIRE-to-ARC Mapping Design

## Key Decisions

— Using `arctrl` directly rather than intermediate dictionaries.
We do not build intermediate JSON/dict representations of the RO-Crate before serializing. The `mapper.py` code instantiates explicit Pydantic-like Python objects from `arctrl` (e.g., `ArcInvestigation`, `ArcStudy`, `ArcAssay`, `ArcTable`, `CompositeCell`) and builds the hierarchy defensively.

> [!NOTE]
> All conceptual design mapping decisions—why spatial elements become protocols or why online resources flatten into Assay tables—are documented globally in [docs/inspire_mapping.md](../../../../docs/inspire_mapping.md).
