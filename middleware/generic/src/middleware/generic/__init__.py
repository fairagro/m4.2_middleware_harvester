"""Generic harvest plugin: Protocol + shared PayloadParser composition.

Discovery units and PayloadParsers are owned by ``middleware.parsing`` and are
deliberately not re-exported here — plugins must import them from the shared
package so no cross-plugin parser edge can form via ``middleware.generic``.
"""

from middleware.generic.config import Config, ProtocolType

__all__ = [
    "Config",
    "ProtocolType",
]
