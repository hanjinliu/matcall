__version__ = "1.2.0.alpha"

__all__ = []

try:
    from .core import MatStruct, translate, eval, addpath, workspace

    __all__ = ["MatStruct", "translate", "eval", "addpath", "workspace"]
except ImportError as e:
    if e.msg.startswith("No module named 'matlab'"):
        import warnings
        warnings.warn(
            "MATLAB Python API not found in paths. Please register path to the "
            "API directory you've downloaded by:"
            ">>> from matcall import register_engine\n"
            ">>> register_engine(path/to/matlab)\n"
            "For more information, see https://jp.mathworks.com/help/matlab/matlab-engine-for-python.html?lang=en",
            UserWarning,
        )
    else:
        raise e

try:
    from .ipython import matlab
except (ImportError, NameError):
    pass
else:
    __all__.append("matlab")

def MatCaller(*args, **kwargs):
    import warnings
    warnings.warn(
        "MatCaller is deprecated and will be removed soon. You no longer have to "
        "construct MatCaller object. Methods 'translate', 'eval', 'addpath' "
        "and 'workspace' are available as functions so that just import them like:\n"
        ">>> from matcall import addpath.",
        DeprecationWarning,
    )
    obj = object()
    obj.translate = translate
    obj.eval = eval
    obj.addpath = addpath
    obj.workspace = workspace



def register_engine(path: str):
    """
    Register path to MATLAB Python API so that you don't have to append its path
    anymore.
    """
    import sys
    from pathlib import Path
    
    save_path = Path(__file__).parent  / "matcall-info.txt"
    sys.path.append(str(path))
    try:
        import matlab.engine as eng
    except ImportError as e:
        if e.msg.startswith("No module named 'matlab'"):
            raise ValueError(
                f"'matlab' module not found at {path!r}. Make sure you've "
                "installed MATLAB Python API at correct path."
            )
        else:
            raise e
    
    with open(save_path, mode="w") as f:
        f.write(path)
