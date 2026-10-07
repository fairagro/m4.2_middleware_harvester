"""Keep ARC comment names unique so the ARC can be written to disk.

ARCtrl's ``ARC.Write`` (Python, 3.2.x) fails with ``TypeError: Object is not iterable`` when an
Investigation, Study, Assay or Person has two Comments with the same name. The API reads every
harvested RO-Crate and writes it with ``ARC.Write``, so a repeated name (several Regal
``associatedDataset`` values, several organisational creators) loses the whole ARC there.
Same-name Comments are therefore merged into one, with their distinct values joined by ``; ``.

ARCtrl also duplicates the ``dateModified`` Comment on every read: it keeps the Comment node
and adds one more from the root ``dateModified``. The RO-Crate is written with the root
property only, so a read gives exactly one Comment.

Both are ARCtrl bugs, reported upstream; remove each workaround once the API's arctrl has the fix:

- duplicate names: https://github.com/nfdi4plants/ARCtrl/issues/641 (``unique_comment_names``)
- duplicated ``dateModified``: https://github.com/nfdi4plants/ARCtrl/issues/642
  (``drop_date_modified_comment_node``); a first-class ``DateModified`` is requested in
  https://github.com/nfdi4plants/ARCtrl/issues/643.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from arctrl import ARC, Comment  # type: ignore[import-untyped]

from middleware.payload.arc_dates import DATE_MODIFIED_COMMENT

VALUE_SEPARATOR = "; "


def merge_duplicate_comments(comments: list[Comment]) -> None:
    """Merge Comments with the same name in place, keeping the first one's position."""
    merged: dict[str, Comment] = {}
    values: dict[str, list[str]] = {}
    kept: list[Comment] = []
    for comment in comments:
        name = comment.Name
        if name is None:
            kept.append(comment)
            continue
        value = comment.Value or ""
        if name not in merged:
            merged[name] = comment
            values[name] = [value] if value else []
            kept.append(comment)
        elif value and value not in values[name]:
            values[name].append(value)
    for name, comment in merged.items():
        comment.Value = VALUE_SEPARATOR.join(values[name]) or None
    comments[:] = kept


def _comment_holders(arc: ARC) -> Iterable[Any]:
    yield arc
    yield from arc.Contacts
    yield from arc.Publications
    for study in arc.Studies:
        yield study
        yield from study.Contacts
        yield from study.Publications
    for assay in arc.Assays:
        yield assay
        yield from assay.Performers


def unique_comment_names(arc: ARC) -> None:
    """Merge same-name Comments on the Investigation and its Studies, Assays, Persons and Publications."""
    for holder in _comment_holders(arc):
        merge_duplicate_comments(holder.Comments)


def drop_date_modified_comment_node(arc_json: str) -> str:
    """Remove the ``dateModified`` Comment node and its references; the root property stays."""
    if f'"{DATE_MODIFIED_COMMENT}"' not in arc_json:
        return arc_json
    crate = json.loads(arc_json)
    graph = crate.get("@graph", [])
    dropped = {
        node["@id"] for node in graph if node.get("@type") == "Comment" and node.get("name") == DATE_MODIFIED_COMMENT
    }
    if not dropped:
        return arc_json
    crate["@graph"] = [node for node in graph if node.get("@id") not in dropped]
    for node in crate["@graph"]:
        refs = node.get("comment")
        if isinstance(refs, list):
            refs = [ref for ref in refs if not (isinstance(ref, dict) and ref.get("@id") in dropped)]
        elif isinstance(refs, dict) and refs.get("@id") in dropped:
            refs = []
        if refs == []:
            node.pop("comment")
        elif refs is not None:
            node["comment"] = refs
    # Compact, like ARCtrl's ToROCrateJsonString.
    return json.dumps(crate, ensure_ascii=False, separators=(",", ":"))
