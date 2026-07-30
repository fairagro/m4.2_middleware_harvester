"""arctrl 3.2+ compatibility helpers.

Requires ``arctrl>=3.2``. In arctrl 3.2 the public names ``CompositeHeader``,
``IOType``, and ``CompositeCell`` are redefined as ``type`` aliases (unions of
tagged cases). That shadows the concrete classes that expose factory methods
such as ``parameter()``, ``input()``, and ``free_text()``.

Import the underscore implementations under the familiar public names so
call sites keep working until upstream restores factories on the public
aliases.
"""

from __future__ import annotations

from arctrl.py.Core.Table.composite_cell import _CompositeCell as CompositeCell
from arctrl.py.Core.Table.composite_header import _CompositeHeader as CompositeHeader, _IOType as IOType

__all__ = ["CompositeCell", "CompositeHeader", "IOType"]
