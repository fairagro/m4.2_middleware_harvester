"""Shared identifier sanitization helpers for ARC Investigation / Study / Assay ids."""

from __future__ import annotations

import re

_FORBIDDEN_ID_CHARS = re.compile(r"[^a-zA-Z0-9 _-]")


def sanitize_identifier(raw: str) -> str:
    """Make *raw* safe for arctrl ``Investigation.identifier``."""
    stripped = re.sub(r"^https?://", "", raw)
    sanitized = _FORBIDDEN_ID_CHARS.sub("_", stripped)
    return re.sub(r"_{2,}", "_", sanitized).strip("_")


def to_identifier_slug(title: str) -> str | None:
    """Slugify a non-empty title for ARC identifiers (max 80 chars)."""
    if not title or not title.strip():
        return None
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:80] or None
