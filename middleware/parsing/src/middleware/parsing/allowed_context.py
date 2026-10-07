"""Shared helpers for ``allowed_context_url`` config and remote IRI matching."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def normalize_context_url(url: str) -> str:
    """Return ``url`` with trailing slashes stripped for allowlist comparison."""
    return url.rstrip("/")


def _allowlist_match_forms(entry: str) -> frozenset[str]:
    """Return comparison forms for one allowlist entry.

    Trailing slashes are ignored. An ``http`` entry also matches the same IRI
    under ``https`` (one-way upgrade); ``https`` does not imply ``http``.
    """
    norm = normalize_context_url(entry)
    forms = {norm}
    parsed = urlparse(norm)
    if parsed.scheme == "http":
        forms.add(urlunparse(parsed._replace(scheme="https")))
    return frozenset(forms)


def validate_allowed_context_url_value(value: object) -> list[str] | None:
    """Coerce a config value to ``list[str] | None``; raise ``ValueError`` if invalid.

    Accepts a single http(s) IRI string, a list of such strings, empty/whitespace
    (treated as unset), or ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        items: list[object] = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("allowed_context_url must be an http(s) URL string or a list of them")

    out: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ValueError("allowed_context_url list entries must be strings")
        stripped = item.strip()
        if not stripped:
            continue
        parsed = urlparse(stripped)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("allowed_context_url must be an absolute http(s) URL with a host")
        out.append(stripped)
    return out or None


def context_url_is_allowed(url: str, allowed: list[str] | None) -> bool:
    """Return whether ``url`` matches the allowlist.

    Matching ignores trailing slashes. When an allowlist entry uses ``http``, the
    same IRI under ``https`` is also accepted; ``https`` entries do not accept
    ``http``. When ``allowed`` is ``None``, every absolute http(s) URL is
    considered allowed (caller still enforces scheme/host).
    """
    if allowed is None:
        return True
    candidate = normalize_context_url(url)
    return any(candidate in _allowlist_match_forms(entry) for entry in allowed)
