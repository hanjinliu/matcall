__version__ = "1.2.0.alpha"

from .core import MatStruct, translate, eval, addpath

__all__ = ["MatStruct", "translate", "eval", "addpath"]

try:
    from .ipython import matlab
except ImportError:
    pass
else:
    __all__.append("matlab")
