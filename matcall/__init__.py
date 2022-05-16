__version__ = "1.2.0.alpha"

from .core import MatStruct, translate, eval, addpath, workspace

__all__ = ["MatStruct", "translate", "eval", "addpath", "workspace"]

try:
    from .ipython import matlab
except (ImportError, NameError):
    pass
else:
    __all__.append("matlab")
