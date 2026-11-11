"""Shared Investigation Comment contract for keyword / classification terms (#603).

ArcInvestigation has no first-class keywords field. Until the API materializes per-term
Comments as Schema.org / DefinedTerm (api#663), mappers write:

* aggregate ``Keywords`` — transitional Search Hub string surface (#604 removes it)
* per-term ``keyword [<URI|label>]`` — durable term identity
* optional ``keyword [DDC:<URI>]`` — classification only when a class URI is known
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from arctrl import ArcInvestigation, Comment  # type: ignore[import-untyped]

AGGREGATE_NAME = "Keywords"
JOIN = ", "


@dataclass(frozen=True, slots=True)
class KeywordSubject:
    """One subject / plain keyword term."""

    label: str
    term_uri: str | None = None


@dataclass(frozen=True, slots=True)
class KeywordClassification:
    """One classification term (e.g. DDC); Comment emitted only when ``class_uri`` is set."""

    label: str
    class_uri: str


def _trim(value: str | None) -> str:
    return (value or "").strip()


def _normalize_subjects(subjects: Sequence[KeywordSubject | tuple[str, str | None]]) -> list[KeywordSubject]:
    out: list[KeywordSubject] = []
    for item in subjects:
        if isinstance(item, KeywordSubject):
            label, uri = item.label, item.term_uri
        else:
            label, uri = item[0], item[1]
        text = _trim(label)
        if not text:
            continue
        uri_text = _trim(uri) or None
        out.append(KeywordSubject(label=text, term_uri=uri_text))
    out.sort(
        key=lambda term: (
            term.label.casefold(),
            term.label,
            (term.term_uri or "").casefold(),
            term.term_uri or "",
        )
    )
    return out


def _normalize_classifications(
    classifications: Sequence[KeywordClassification | tuple[str, str]],
) -> list[KeywordClassification]:
    out: list[KeywordClassification] = []
    for item in classifications:
        if isinstance(item, KeywordClassification):
            label, uri = item.label, item.class_uri
        else:
            label, uri = item[0], item[1]
        text = _trim(label)
        uri_text = _trim(uri)
        if not text or not uri_text:
            continue
        out.append(KeywordClassification(label=text, class_uri=uri_text))
    out.sort(
        key=lambda term: (
            term.label.casefold(),
            term.label,
            term.class_uri.casefold(),
            term.class_uri,
        )
    )
    return out


def _dedupe_labels(subjects: Iterable[KeywordSubject]) -> list[str]:
    by_fold: dict[str, str] = {}
    for term in subjects:
        fold = term.label.casefold()
        if fold not in by_fold:
            by_fold[fold] = term.label
    return sorted(by_fold.values(), key=lambda value: (value.casefold(), value))


def _subject_comment_name(term: KeywordSubject) -> str:
    if term.term_uri:
        return f"keyword [{term.term_uri}]"
    return f"keyword [{term.label}]"


def _append_subject_comments(
    inv: ArcInvestigation,
    subjects: list[KeywordSubject],
    *,
    seen_names: set[str],
) -> None:
    seen_plain_folds: set[str] = set()
    for term in subjects:
        name = _subject_comment_name(term)
        if term.term_uri is None:
            fold = term.label.casefold()
            if fold in seen_plain_folds:
                continue
            seen_plain_folds.add(fold)
        if name in seen_names:
            continue
        seen_names.add(name)
        inv.Comments.append(Comment.create(name, term.label))


def _append_classification_comments(
    inv: ArcInvestigation,
    classifications: list[KeywordClassification],
    *,
    seen_names: set[str],
) -> None:
    for term in classifications:
        name = f"keyword [DDC:{term.class_uri}]"
        if name in seen_names:
            continue
        seen_names.add(name)
        inv.Comments.append(Comment.create(name, term.label))


def add_keyword_comments(
    inv: ArcInvestigation,
    *,
    subjects: Sequence[KeywordSubject | tuple[str, str | None]] = (),
    classifications: Sequence[KeywordClassification | tuple[str, str]] = (),
) -> None:
    """Append aggregate + per-term (+ optional DDC) Comments to ``inv``.

    Subject/plain labels feed the aggregate. Classification labels never join into
    ``Keywords``. Comment names are unique within this call (first kept after stable sort).
    """
    normalized = _normalize_subjects(subjects)
    labels = _dedupe_labels(normalized)
    if labels:
        inv.Comments.append(Comment.create(AGGREGATE_NAME, JOIN.join(labels)))

    seen_names: set[str] = {AGGREGATE_NAME} if labels else set()
    _append_subject_comments(inv, normalized, seen_names=seen_names)
    _append_classification_comments(
        inv,
        _normalize_classifications(classifications),
        seen_names=seen_names,
    )
