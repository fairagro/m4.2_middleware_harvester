"""Stable RDF access layer for linked-data vocabulary mappers.

Mappers read graphs through :class:`ResourceView` / :class:`StableText` so
parser-local blank-node labels and rdflib iteration order do not leak into ARC
fields. Discovery context (:class:`~.linked_data_mapper.MappingContext`) is
intentionally not part of this module.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF
from rdflib.term import BNode, Node

SCHEMA_ORG_NAMESPACES: tuple[Namespace, ...] = (
    Namespace("https://schema.org/"),
    Namespace("http://schema.org/"),
)

_DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", re.IGNORECASE)
_STABLE_BNODE_MAX_DEPTH = 2


@dataclass(frozen=True)
class StableText:
    """Trimmed text that is never a blank-node label."""

    value: str

    def __str__(self) -> str:
        """Return the trimmed text value."""
        return self.value


@dataclass(frozen=True)
class LabelledNode:
    """Label from configured predicates; ``stable_id`` only for real IRIs."""

    label: StableText
    stable_id: str | None


@dataclass(frozen=True)
class StableGraphPolicy:
    """Wrap-time policies for label lookup and local-name term aliases."""

    label_predicates: tuple[Node, ...]
    #: Namespaces used by ``schema_*`` / term helpers (any vocabulary, not Schema.org-only).
    term_namespaces: tuple[Namespace, ...] = ()


class StableGraph:
    """Wrapper over :class:`rdflib.Graph` that yields :class:`ResourceView` handles."""

    def __init__(self, graph: Graph, policy: StableGraphPolicy) -> None:
        """Bind an rdflib graph and access policy."""
        self._graph = graph
        self._policy = policy

    @classmethod
    def wrap(
        cls,
        graph: Graph,
        *,
        label_predicates: Iterable[Node] | None = None,
        term_namespaces: Iterable[Namespace] | None = None,
    ) -> StableGraph:
        """Wrap ``graph`` with optional label predicates and term-alias namespaces.

        Vocabulary-specific defaults (e.g. Schema.org http/https) belong at the
        mapper call site — pass ``SCHEMA_ORG_NAMESPACES`` explicitly — not as
        StableGraph flags.
        """
        return cls(
            graph,
            StableGraphPolicy(
                label_predicates=tuple(label_predicates) if label_predicates is not None else (),
                term_namespaces=tuple(term_namespaces) if term_namespaces is not None else (),
            ),
        )

    @property
    def graph(self) -> Graph:
        """Underlying rdflib graph."""
        return self._graph

    @property
    def policy(self) -> StableGraphPolicy:
        """Active wrap policy (labels and namespace aliases)."""
        return self._policy

    def view(self, subject: Node) -> ResourceView:
        """Return a ResourceView for ``subject``."""
        return ResourceView(self, subject)

    def sort_key(self, node: Node) -> tuple[int, str]:
        """Stable sort key for ``node`` (never ranks by blank-node labels)."""
        return self.view(node).sort_key()

    def object_text(self, node: Node | None) -> str | None:
        """Stable display text for ``node``; never a blank-node label."""
        if node is None:
            return None
        return self.view(node).object_text()


class ResourceView:
    """Opaque handle for a subject; ``iri`` is None for blank nodes."""

    def __init__(self, stable: StableGraph, subject: Node) -> None:
        """Bind this view to ``subject`` within ``stable``."""
        self._stable = stable
        self._subject = subject

    @property
    def node(self) -> Node:
        """Underlying rdflib node (for type checks and ARC assembly)."""
        return self._subject

    @property
    def iri(self) -> str | None:
        """Public IRI of this subject, or None for blank nodes."""
        if isinstance(self._subject, BNode):
            return None
        if isinstance(self._subject, URIRef):
            text = str(self._subject).strip()
            return text or None
        return None

    def is_type(self, rdf_type: Node) -> bool:
        """Return True when this subject has ``rdf:type`` ``rdf_type``."""
        return (self._subject, RDF.type, rdf_type) in self._stable.graph

    def literal(self, *predicates: Node) -> StableText | None:
        """Singular literal pick (language policy); never a blank-node label."""
        chosen = self._choose_literal(self._literal_objects(*predicates))
        if chosen is None:
            return None
        return StableText(str(chosen).strip())

    def literals(self, *predicates: Node) -> list[StableText]:
        """Deduped, stably sorted literal texts."""
        by_fold: dict[str, str] = {}
        for lit in self._literal_objects(*predicates):
            text = str(lit).strip()
            if not text:
                continue
            fold = text.casefold()
            previous = by_fold.get(fold)
            if previous is None or text < previous:
                by_fold[fold] = text
        return [StableText(value) for value in sorted(by_fold.values(), key=lambda v: (v.casefold(), v))]

    def resource(self, *predicates: Node, of_type: Node | None = None) -> ResourceView | None:
        """Singular resource pick with deterministic ranking."""
        nodes = self.resources(*predicates, of_type=of_type)
        return nodes[0] if nodes else None

    def resources(self, *predicates: Node, of_type: Node | None = None) -> list[ResourceView]:
        """Resource objects in deterministic order; never ranked by BNode labels."""
        graph = self._stable.graph
        non_literals = [obj for obj in self._all_objects(*predicates) if not isinstance(obj, Literal)]
        if of_type is not None:
            non_literals = [obj for obj in non_literals if (obj, RDF.type, of_type) in graph]
        ordered = sorted(non_literals, key=self._stable.sort_key)
        return [ResourceView(self._stable, node) for node in ordered]

    def text(self, *predicates: Node) -> str | None:
        """Soft-lift of Schema.org ``_str``: literal preferred, else URIRef string.

        Never returns a blank-node label.
        """
        value = self.object_node(*predicates)
        if value is None or isinstance(value, BNode):
            return None
        text = str(value)
        return text.strip() if isinstance(value, Literal) else text

    def texts(self, *predicates: Node) -> list[str]:
        """Soft-lift of Schema.org ``_strs``: literals, URIRefs, labelled blanks."""
        by_fold: dict[str, str] = {}
        for obj in self._all_objects(*predicates):
            text = self._stable.object_text(obj)
            if not text:
                continue
            fold = text.casefold()
            previous = by_fold.get(fold)
            if previous is None or text < previous:
                by_fold[fold] = text
        return sorted(by_fold.values(), key=lambda value: (value.casefold(), value))

    def object_node(self, *predicates: Node) -> Node | None:
        """Soft-lift of Schema.org ``_obj``: literal preferred, else ranked resource."""
        objects = self._all_objects(*predicates)
        if not objects:
            return None
        chosen_literal = self._choose_literal([obj for obj in objects if isinstance(obj, Literal)])
        if chosen_literal is not None:
            return chosen_literal
        non_literals = [obj for obj in objects if not isinstance(obj, Literal)]
        if not non_literals:
            return None
        return sorted(non_literals, key=self._stable.sort_key)[0]

    def schema_objects(self, term: str) -> list[Node]:
        """Objects for a Schema.org term under configured http/https namespaces."""
        namespaces = self._stable.policy.term_namespaces
        if not namespaces:
            return []
        seen: set[Node] = set()
        objects: list[Node] = []
        for schema in namespaces:
            predicate = getattr(schema, term)
            for obj in self._stable.graph.objects(self._subject, predicate):
                if obj not in seen:
                    seen.add(obj)
                    objects.append(obj)
        return objects

    def schema_text(self, term: str) -> str | None:
        """``text`` over dual Schema.org namespaces for ``term``."""
        predicates = self._schema_predicates(term)
        return self.text(*predicates) if predicates else None

    def __getitem__(self, term: str) -> str | None:
        """Schema.org term sugar: ``view["name"]`` ≡ ``view.schema_text("name")``."""
        if not isinstance(term, str):
            raise TypeError(f"ResourceView keys must be str term names, got {type(term).__name__}")
        return self.schema_text(term)

    def schema_texts(self, term: str) -> list[str]:
        """``texts`` over dual Schema.org namespaces for ``term``."""
        predicates = self._schema_predicates(term)
        return self.texts(*predicates) if predicates else []

    def schema_literal(self, term: str) -> StableText | None:
        """``literal`` over dual Schema.org namespaces for ``term``."""
        predicates = self._schema_predicates(term)
        return self.literal(*predicates) if predicates else None

    def schema_object_node(self, term: str) -> Node | None:
        """``object_node`` over dual Schema.org namespaces for ``term``."""
        predicates = self._schema_predicates(term)
        return self.object_node(*predicates) if predicates else None

    def schema_resources(self, term: str, *, of_type: Node | None = None) -> list[ResourceView]:
        """``resources`` over dual Schema.org namespaces for ``term``."""
        predicates = self._schema_predicates(term)
        return self.resources(*predicates, of_type=of_type) if predicates else []

    def schema_is_type(self, term: str) -> bool:
        """Return True when subject has ``rdf:type`` ``term`` in any term namespace."""
        return any(self.is_type(getattr(namespace, term)) for namespace in self._stable.policy.term_namespaces)

    def labelled(self, *predicates: Node) -> list[LabelledNode]:
        """Labelled objects; skip unlabelled blank nodes; never use ``str(BNode)``."""
        results: list[LabelledNode] = []
        for obj in self._all_objects(*predicates):
            if isinstance(obj, Literal):
                text = str(obj).strip()
                if text:
                    results.append(LabelledNode(StableText(text), None))
                continue
            label = self._label_for(obj)
            if isinstance(obj, URIRef):
                iri = str(obj).strip()
                display = label or iri
                if display:
                    results.append(LabelledNode(StableText(display), iri or None))
                continue
            if isinstance(obj, BNode) and label:
                results.append(LabelledNode(StableText(label), None))
        return results

    def http_iri(self) -> str | None:
        """HTTP(S) IRI of this subject; blank node → None."""
        return http_iri(self._subject)

    def doi(self) -> str | None:
        """DOI from this node (literal, IRI, or typed Schema.org PropertyValue).

        PropertyValue extraction requires ``rdf:type`` PropertyValue in a
        configured term namespace plus DOI ``propertyID`` / ``value``. This is
        graph structure reading, not ARC identifier policy — cascade stays
        in the vocabulary mapper.
        """
        return doi_from_node(self._stable, self._subject)

    def dois_from(self, *predicates: Node) -> list[str]:
        """Collect DOIs from objects of ``predicates`` (deduped, casefold-sorted)."""
        by_fold: dict[str, str] = {}
        for obj in self._all_objects(*predicates):
            doi = doi_from_node(self._stable, obj)
            if not doi:
                continue
            fold = doi.casefold()
            previous = by_fold.get(fold)
            if previous is None or doi < previous:
                by_fold[fold] = doi
        return sorted(by_fold.values(), key=lambda doi: (doi.casefold(), doi))

    def schema_dois(self, term: str = "identifier") -> list[str]:
        """Collect DOIs from Schema.org ``term`` objects (and subject IRI if DOI-like)."""
        by_fold: dict[str, str] = {}
        for obj in self.schema_objects(term):
            doi = doi_from_node(self._stable, obj)
            if not doi:
                continue
            fold = doi.casefold()
            previous = by_fold.get(fold)
            if previous is None or doi < previous:
                by_fold[fold] = doi
        if isinstance(self._subject, URIRef):
            subject_doi = normalize_doi(str(self._subject))
            if subject_doi:
                fold = subject_doi.casefold()
                previous = by_fold.get(fold)
                if previous is None or subject_doi < previous:
                    by_fold[fold] = subject_doi
        return sorted(by_fold.values(), key=lambda doi: (doi.casefold(), doi))

    def _schema_predicates(self, term: str) -> tuple[Node, ...]:
        return tuple(getattr(ns, term) for ns in self._stable.policy.term_namespaces)

    def _all_objects(self, *predicates: Node) -> list[Node]:
        if not predicates:
            return []
        seen: set[Node] = set()
        objects: list[Node] = []
        graph = self._stable.graph
        for predicate in predicates:
            for obj in graph.objects(self._subject, predicate):
                if obj not in seen:
                    seen.add(obj)
                    objects.append(obj)
        return objects

    def _literal_objects(self, *predicates: Node) -> list[Literal]:
        return [obj for obj in self._all_objects(*predicates) if isinstance(obj, Literal)]

    def _label_for(self, obj: Node) -> str | None:
        view = ResourceView(self._stable, obj)
        labels = self._stable.policy.label_predicates
        if not labels:
            return None
        name_node = view.object_node(*labels)
        if isinstance(name_node, Literal):
            text = str(name_node).strip()
            return text or None
        if isinstance(name_node, URIRef):
            text = str(name_node).strip()
            return text or None
        return None

    def object_text(self) -> str | None:
        """Stable display text for this subject; never a blank-node label."""
        return self._object_text_for(self._subject)

    def sort_key(self) -> tuple[int, str]:
        """Stable sort key for this subject (never ranks by blank-node labels)."""
        return self._node_sort_key(self._subject)

    def _object_text_for(self, obj: Node) -> str | None:
        if isinstance(obj, Literal):
            text = str(obj).strip()
            return text or None
        if isinstance(obj, URIRef):
            text = str(obj).strip()
            return text or None
        if isinstance(obj, BNode):
            return self._label_for(obj)
        return None

    def _node_sort_key(
        self,
        node: Node,
        *,
        _depth: int = 0,
        _visiting: frozenset[Node] | None = None,
    ) -> tuple[int, str]:
        graph = self._stable.graph
        if isinstance(node, URIRef):
            return (0, str(node))
        if isinstance(node, BNode):
            visiting = _visiting or frozenset()
            if node in visiting or _depth > _STABLE_BNODE_MAX_DEPTH:
                return (1, "")
            next_visiting = visiting | {node}
            parts: list[tuple[str, str]] = []
            for predicate, obj in graph.predicate_objects(node):
                pred_token = _stable_term_token(predicate)
                if pred_token is None:
                    continue
                if isinstance(obj, BNode):
                    nested_sig = self._node_sort_key(
                        obj,
                        _depth=_depth + 1,
                        _visiting=next_visiting,
                    )[1]
                    parts.append((pred_token, f"bnode:{nested_sig}"))
                else:
                    obj_token = _stable_term_token(obj)
                    if obj_token is not None:
                        parts.append((pred_token, obj_token))
            return (1, repr(tuple(sorted(parts))))
        return (2, str(node))

    @staticmethod
    def _lang_rank(literal: Literal) -> int:
        lang = (literal.language or "").casefold()
        if lang == "en" or lang.startswith("en-"):
            return 0
        if lang == "de" or lang.startswith("de-"):
            return 1
        if lang == "":
            return 2
        return 3

    @classmethod
    def _choose_literal(cls, literals: list[Literal]) -> Literal | None:
        best: Literal | None = None
        best_key: tuple[int, int, str, str, str, str] | None = None
        for literal in literals:
            text = str(literal).strip()
            if not text:
                continue
            lang = (literal.language or "").casefold()
            datatype = str(literal.datatype) if literal.datatype is not None else ""
            key = (
                cls._lang_rank(literal),
                -len(text),
                text.casefold(),
                text,
                lang,
                datatype,
            )
            if best_key is None or key < best_key:
                best_key = key
                best = literal
        return best


def http_iri(node: Node) -> str | None:
    """Return an http(s) IRI string, or None for blank nodes / non-HTTP values."""
    if isinstance(node, BNode):
        return None
    if isinstance(node, (Literal, URIRef)):
        text = str(node).strip()
        if text.startswith(("http://", "https://")):
            return text
    return None


def normalize_doi(raw: str) -> str | None:
    """Normalize a DOI string; return None when not a ``10.…/…`` DOI."""
    text = _DOI_PREFIX_RE.sub("", raw.strip()).strip()
    if text.startswith("10.") and "/" in text:
        return text
    return None


def doi_from_node(stable: StableGraph, node: Node) -> str | None:
    """Extract a DOI from a literal, IRI, or typed Schema.org PropertyValue node."""
    if isinstance(node, Literal):
        return normalize_doi(str(node))
    if isinstance(node, URIRef):
        doi = normalize_doi(str(node))
        if doi:
            return doi
        return _doi_from_property_value(stable, node)
    if isinstance(node, BNode):
        return _doi_from_property_value(stable, node)
    return None


def _stable_object_texts(objects: list[Node]) -> list[str]:
    """Return stripped texts from Literal/URIRef objects; skip blank nodes."""
    texts: list[str] = []
    for obj in objects:
        if isinstance(obj, BNode) or not isinstance(obj, (Literal, URIRef)):
            continue
        text = str(obj).strip()
        if text:
            texts.append(text)
    return texts


def _doi_from_property_value(stable: StableGraph, node: Node) -> str | None:
    if not stable.policy.term_namespaces:
        # Require schema aliases for PropertyValue extraction.
        return None
    view = ResourceView(stable, node)
    if not view.schema_is_type("PropertyValue"):
        return None
    property_ids = _stable_object_texts(view.schema_objects("propertyID"))
    values = _stable_object_texts(view.schema_objects("value"))
    if not values or not property_ids:
        return None
    if not any("doi" in pid.lower() for pid in property_ids):
        return None
    for value in values:
        doi = normalize_doi(value)
        if doi:
            return doi
    return None


def _stable_term_token(term: Node) -> str | None:
    if isinstance(term, BNode):
        return None
    if isinstance(term, URIRef):
        text = str(term).strip()
        return repr(("uri", text)) if text else None
    if isinstance(term, Literal):
        text = str(term).strip()
        if not text:
            return None
        lang = (term.language or "").casefold()
        datatype = str(term.datatype) if term.datatype is not None else ""
        return repr(("lit", text, lang, datatype))
    text = str(term).strip()
    return text or None
