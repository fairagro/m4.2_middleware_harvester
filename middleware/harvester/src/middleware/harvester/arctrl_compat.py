"""arctrl 3.2+ compatibility helpers.

Requires ``arctrl>=3.2``. In arctrl 3.2 the public names ``CompositeHeader``,
``IOType``, and ``CompositeCell`` are redefined as ``type`` aliases (unions of
tagged cases). That shadows the concrete classes that expose factory methods
such as ``parameter()``, ``input()``, and ``free_text()``.

Import the underscore implementations under the familiar public names so
call sites keep working until upstream restores factories on the public
aliases.

Also patches ``fable_library.util.string_hash``: with fable-library 5.13 the
djb2 loop uses unbounded Python ``int`` and only wraps at the end via
``int32(h)``, which raises ``TypeError: Cannot convert argument of type int
to Int32`` for strings longer than ~200 characters. ArcTable FreeText cells
trigger that path (e.g. joined INSPIRE online-resource URLs). Keep the hash
arithmetic in ``int32`` for the whole loop until upstream fixes it.
"""

from __future__ import annotations

import fable_library.util as _fable_util
from arctrl.py.Core.Table.composite_cell import _CompositeCell as CompositeCell
from arctrl.py.Core.Table.composite_header import _CompositeHeader as CompositeHeader, _IOType as IOType
from fable_library.core import int32


def _string_hash_int32(s: str) -> int32:
    """djb2 hash with wrapping Int32 arithmetic (F# ``int`` semantics)."""
    h = int32(5381)
    thirty_three = int32(33)
    for c in s:
        h = (h * thirty_three) ^ int32(ord(c))
    return h


_fable_util.string_hash = _string_hash_int32

__all__ = ["CompositeCell", "CompositeHeader", "IOType"]
