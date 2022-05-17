from __future__ import annotations
from typing import TYPE_CHECKING, MutableMapping, Any, Iterable

if TYPE_CHECKING:
    class MatlabEngine:
        def eval(self, expr: str, nargout: int) -> Any: ...
        def feval(self, f: Any, *args) -> Any: ...
        def evalc(self, expr: str) -> str: ...
        def addpath(self, path: str) -> None: ...
        def nargout(self, f: Any) -> int: ...
        def func2str(self, f : Any) -> str: ...
        def table2struct(self, table: Any) -> Any: ...
        def properties(self, obj: Any, nargout: int) -> Iterable[str]: ...
        def methods(self, obj: Any, nargout: int) -> Iterable[str]: ...
        def struct2table(self, obj: Any) -> Any: ...
        
        workspace: MutableMapping[str, Any]
        
    ENGINE = MatlabEngine()
    
    from array import array as pyarray
    
    class MatObject:
        """
        MATLAB object that cannot be converted into a Python object will provide
        MATLAB-Python interface via this object.
        """
    
    class MatlabExecutionError(RuntimeError):
        """Exception inside MATLAB will raise this error on Python side."""

    class MLArray:
        """Just for typing."""
        def __init__(
            self,
            initializer: list | None = None,
            size=None,
            is_complex: bool = False,
        ):
            ...
        
        _real: pyarray
        _imag: pyarray
        _data: pyarray
        _size: tuple[int, ...]
        _strides: list[int]
        size: tuple[int, ...]

    class ml_double(MLArray): pass
    class ml_single(MLArray): pass
    class ml_uint8(MLArray): pass
    class ml_int8(MLArray): pass
    class ml_uint16(MLArray): pass
    class ml_int16(MLArray): pass
    class ml_uint32(MLArray): pass
    class ml_int32(MLArray): pass
    class ml_uint64(MLArray): pass
    class ml_int64(MLArray): pass
    class ml_bool(MLArray): pass
    
else:
    import matlab.engine as eng
    from matlab.engine import MatlabExecutionError
    ENGINE = eng.start_matlab()

    from matlab import object as MatObject
    from matlab import (
        double as ml_double,
        single as ml_single,
        uint8 as ml_uint8,
        int8 as ml_int8,
        uint16 as ml_uint16,
        int16 as ml_int16, 
        uint32 as ml_uint32,
        int32 as ml_int32,
        uint64 as ml_uint64,
        int64 as ml_int64,
        logical as ml_bool,
    )

def ml_complex64(*args, **kwargs):
    return ml_single(*args, **kwargs, is_complex=True)

def ml_complex128(*args, **kwargs):
    return ml_double(*args, **kwargs, is_complex=True)

ml_complex64.__name__ = "complex64"
ml_complex128.__name__ = "complex128"