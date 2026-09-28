## Key Decisions

### The fallback lives in `ResourceView`, not in the mapper's field readers

`GeneralSchemaOrgMapper` reads roughly twenty properties off the Dataset subject, every one of them through
`self.view(subject)`. `ResourceView` funnels all predicate access — `literal`, `literals`, `resource`, `resources`,
`text`, `texts`, `object_node` and every `schema_*` helper — through the single private `_all_objects`. Putting the
fallback there covers all of them at once.

**Reasoning:** the alternative is twenty conditional reads in the mapper, each an opportunity to forget one and each
obscuring the mapping rules with plumbing. One funnel is also one place to test. The cost is that `ResourceView`, which
is deliberately a thin deterministic-access DSL, now carries a resolution policy; that is acceptable because the policy
is purely positional (try subjects in order) and holds no vocabulary knowledge — `isBasedOn` is named only by the
mapper that builds the chain.

### Per-property, first-non-empty-wins; never merged

If the Dataset has one author and the `isBasedOn` paper has twelve, the ARC gets the Dataset's one author, not thirteen.

**Reasoning:** merging invents a fact. A dataset that names its own creator has answered the question, and silently
appending the paper's author list would misattribute the data. Falling back only into a genuine void keeps the
fallback conservative and keeps the outcome explainable in one sentence to a data steward.

### Identity never falls back

`node`, `iri` and `is_type` are bound to the primary subject and ignore the chain.

**Reasoning:** the ARC is about the Dataset. If identity could drift to the paper, `Investigation.identifier` and the
RO-Crate `@id` would silently start describing a different resource, and two Datasets derived from the same paper would
collide. Keeping identity pinned also means `_plan_investigation_identifier` needs no special-casing: it resolves via
`_resolve_graph_url_identifier` from the Dataset's own IRI, as it already does.

### Views handed out by the chain are plain

`resources()` constructs `ResourceView(self._stable, node)` without the chain, so a `Person` reached through the
fallback does not itself inherit it.

**Reasoning:** the chain answers "what does this Dataset say about itself". Once traversal has left the Dataset, the
question no longer applies, and an inherited chain would let an unrelated nested node borrow the paper's fields — the
kind of quiet cross-contamination that is very hard to see in a diff of ARC output.

### DOI falls back on "no parsed DOI", not "no objects"

`schema_dois` / `dois_from` get their own fallback condition rather than inheriting `_all_objects`'.

**Reasoning:** this is the one case where the two conditions genuinely differ, and it is the common case for the source
that motivated the change. A BonaRes record has a `schema:identifier` node — a `PropertyValue` carrying a url — so the
predicate is occupied and a purely predicate-level check would conclude "the Dataset answered" and stop, while the
Dataset in fact yields zero DOIs. The user-visible contract is "fall back when the Dataset provides no usable value",
and for DOIs "usable" means parseable as a DOI.

### The fallback is recorded on the ARC, never silent

Each property resolved through the chain appends an Investigation Comment naming the property and `isBasedOn`, the same
way a title fallback appends `"Title Source"`.

**Reasoning:** the repository's standing rule is that degraded or inferred provenance is surfaced rather than logged
and forgotten. A steward reading an ARC must be able to tell "this description came from the paper the dataset is based
on" from "the provider wrote this description for the dataset". Without the Comment the two are indistinguishable, and
the fallback would quietly launder thin metadata into apparently rich metadata.

### One hop only

An `isBasedOn` target's own `isBasedOn` is not followed.

**Reasoning:** unbounded traversal needs cycle detection and makes provenance unexplainable ("this author came from a
paper cited by a paper the dataset is based on"). One hop covers the observed shape; depth can be revisited if a real
source ever needs it.
