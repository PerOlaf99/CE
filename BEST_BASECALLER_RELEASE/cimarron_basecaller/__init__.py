"""
cimarron_basecaller: a from-scratch base-calling implementation for
MegaBACE 1000 CE raw trace data, informed by (but not limited to) the
publicly disclosed algorithm in EP0944739A1 (Cimarron base caller
patent, application withdrawn -- no patent was ever granted).

RECOMMENDED ENTRY POINT: `track_bases` (empirically tuned, validated
against real Cimarron 3.12 ground truth -- see README for current
accuracy). The original patent-literal reimplementation is still
available as `basecall` but scores far worse in practice; see README.
"""

from .pipeline import basecall, BaseCallResult
from .spacing_caller import track_bases, TrackedBase
from .dp_caller import dp_call_bases
from .simple_caller import call_bases
from .windowed import (
    WindowSpec,
    discover_windows,
    track_bases_windowed,
    call_windows_gui_path,
)

__all__ = [
    "basecall",
    "BaseCallResult",
    "track_bases",
    "TrackedBase",
    "dp_call_bases",
    "call_bases",
    "WindowSpec",
    "discover_windows",
    "track_bases_windowed",
    "call_windows_gui_path",
]
__version__ = "0.3.0"
