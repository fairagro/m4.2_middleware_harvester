# INSPIRE-to-ARC Mapping Design

## Key Decisions

— Using `arctrl` directly rather than intermediate dictionaries.
We do not build intermediate JSON/dict representations of the RO-Crate before serializing. The `mapper.py` code instantiates explicit Pydantic-like Python objects from `arctrl` (e.g., `ArcInvestigation`, `ArcStudy`, `ArcAssay`, `ArcTable`, `CompositeCell`) and builds the hierarchy defensively.

> [!NOTE]
> All conceptual design mapping decisions—why spatial elements become protocols or why online resources flatten into Assay tables—are documented globally in [docs/inspire_mapping.md](../../../../docs/inspire_mapping.md).

## Key Decision: Hierarchy Level Handling

**Problem**: INSPIRE metadata contains a `hierarchyLevel` field describing the scope of the metadata record.

**Solution**:

- **dataset**: Normal mapping to Investigation/Study/Assay
- **nonGeographicDataset**: Normal mapping, but without Spatial Sampling protocol
- **series, collection**: Currently ignored (planned for future implementation)
- **tile**: Ignored (spatial tiles are not harvested)
- **service, model, application**: Ignored (no scientific relevance)

**Implementation**:

```python
# Skip Spatial Sampling for non-geographic datasets
if record.hierarchy and record.hierarchy.lower() == "nongeographicdataset":
    return None

# Document non-standard hierarchy levels
if record.hierarchy and record.hierarchy.lower() not in ["dataset", "nongeographicdataset"]:
    comments.append(Comment.create("Hierarchy Level", record.hierarchy))
```

**Rationale**:

- Follows the mapping specification in [docs/inspire_mapping.md](../../../../docs/inspire_mapping.md)
- Aligns with current architectural limitations
- Provides clear path for future hierarchical dataset support

## Key Decision: Implementation Patterns

**Problem**: The INSPIRE-to-ARC mapping requires handling of complex nested structures and optional fields while maintaining code quality and type safety.

**Solution**: Follow these implementation patterns:

1. **Defensive Programming**: Check for None/empty values before processing
2. **Modular Methods**: Each mapping responsibility has its own method
3. **Type Safety**: Use proper type annotations and handle edge cases
4. **Ontology Integration**: Use OntologyAnnotation for semantic mapping

**Implementation Examples**:

```python
# Defensive role mapping with ontology integration
def _add_role(self, person: Person, contact: Contact) -> None:
    if not contact.role:
        return

    role_mapping = {
        "author": ("Author", "http://purl.obolibrary.org/obo/NCIT_C70909", "NCIT"),
        # ... other role mappings
    }

    mapped_role = role_mapping.get(contact.role.lower(), (contact.role, None, None))
    role_name, tan, tsr = mapped_role

    if tan and tsr:
        person.Roles.append(OntologyAnnotation(name=role_name, tan=tan, tsr=tsr))
    else:
        person.Roles.append(OntologyAnnotation(name=role_name))

# Protocol creation with parameter handling
def _create_data_processing_protocol(self, record: InspireRecord) -> ArcTable | None:
    table = ArcTable.init("Data Processing")
    headers = []
    cells = []

    if record.lineage:
        headers.append(CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")))
        cells.append(CompositeCell.term(OntologyAnnotation(name=record.lineage[:500])))

    if record.lineage_url:
        headers.append(CompositeHeader.parameter(OntologyAnnotation(name="Lineage Documentation URL")))
        cells.append(CompositeCell.term(OntologyAnnotation(name=record.lineage_url)))
    # ... other parameters
```

**Rationale**:

- Ensures robust handling of incomplete metadata
- Maintains clean separation of concerns
- Enables proper semantic mapping with ontologies
- Follows FAIR principles for scientific data

## Key Decision: Ontology Source Management

**Problem**: Proper semantic mapping requires ontology source references for term resolution.

**Solution**: Add common ontology sources to Investigation.OntologySourceReferences:

```python
common_ontologies = [
    ("NCIT", "http://purl.obolibrary.org/obo/ncit.owl", "NCI Thesaurus"),
    ("GEMET", "http://www.eionet.europa.eu/gemet", "GEMET Thesaurus"),
    ("EDAM", "http://edamontology.org", "EDAM Bioinformatics Ontology"),
    ("ISO", "http://www.isotc211.org/2005/gco", "ISO Geospatial Metadata"),
]
```

**Rationale**:

- Enables proper resolution of ontology terms
- Supports multiple domain-specific ontologies
- Follows RO-Crate best practices
- Ensures interoperability with other systems

## Key Decision: Dataset URI and Lineage URL Handling

**Problem**: INSPIRE provides direct URIs to datasets (`dataset_uri`) and lineage documentation (`lineage_url`) that need proper semantic mapping.

**Solution**:

- **Dataset URI**: Add to Assay Annotation Table as "Dataset Landing Page"
- **Lineage URL**: Add as parameter "Lineage Documentation URL" to Data Processing protocol
- **AggregationInfo**: Document as Investigation comment (opaque field)

**Implementation**:

```python
# In _create_assay_table:
if record.dataset_uri:
    outputs.append(("Dataset Landing Page", record.dataset_uri))

# In _create_data_processing_protocol:
if record.lineage_url:
    headers.append(CompositeHeader.parameter(OntologyAnnotation(name="Lineage Documentation URL")))
    cells.append(CompositeCell.term(OntologyAnnotation(name=record.lineage_url)))
```

**Rationale**:

- Dataset URIs represent direct access to the actual data
- Lineage URLs provide provenance documentation
- Both are scientifically relevant and should be properly mapped
- Follows the mapping specification in [docs/inspire_mapping.md](../../../../docs/inspire_mapping.md)
