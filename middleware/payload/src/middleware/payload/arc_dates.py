"""Source modification date on the ARC Investigation.

ARCtrl has no Investigation field for it, but writes an Investigation Comment named
``dateModified`` as the RO-Crate root ``dateModified`` and reads it back into that Comment
(``arctrl.py.Conversion.date_time.date_modified_key``). Only source dates go here, never the
harvest time: that is ``sdDatePublished``.
"""

from __future__ import annotations

from arctrl import Comment  # type: ignore[import-untyped]

from middleware.payload.iso_dates import iso_date

DATE_MODIFIED_COMMENT = "dateModified"


def date_modified_comment(value: str | None) -> Comment | None:
    """Return the ``dateModified`` Comment for an ISO 8601 (or Java ``Date``) ``value``, else ``None``."""
    date = iso_date(value)
    return Comment.create(DATE_MODIFIED_COMMENT, date) if date else None
