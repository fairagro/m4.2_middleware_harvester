"""Geographic helpers shared by payload mappers."""

from __future__ import annotations


def bounding_box(
    west: float | str | None,
    south: float | str | None,
    east: float | str | None,
    north: float | str | None,
) -> str | None:
    """Return a ``Bounding Box`` ParameterValue ``south west north east``, or ``None``.

    Study ParameterValue ``Bounding Box`` uses this axis order so catalog consumers need not
    guess source encodings (INSPIRE west/south/east/north, PhenoRoam W/E/S/N, …). The string is
    compatible with schema.org ``GeoShape.box``; that compatibility is documentation, not a
    Schema.org-specific API. All four sides must parse as floats; otherwise omit the box.
    """
    try:
        w = float(west) if west is not None and str(west).strip() != "" else None
        s = float(south) if south is not None and str(south).strip() != "" else None
        e = float(east) if east is not None and str(east).strip() != "" else None
        n = float(north) if north is not None and str(north).strip() != "" else None
    except (TypeError, ValueError):
        return None
    if w is None or s is None or e is None or n is None:
        return None
    return f"{s} {w} {n} {e}"
