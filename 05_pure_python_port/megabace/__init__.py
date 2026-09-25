"""megabace: basecalling for MegaBACE 1000 RSD files."""

from .basecall import BaseCaller
from .rsd import RSDError, RsdFile, extract_traces

__version__ = "0.1.0"

__all__ = ["BaseCaller", "RSDError", "RsdFile", "extract_traces", "__version__"]
