from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike
from array import array as pyarray
from typing import Protocol, TYPE_CHECKING

from ._const import PYARRAY_TYPE_MAP, DTYPE_MAP_INV, DTYPE_MAP

if TYPE_CHECKING:
    class MLArray(Protocol):
        """Just for typing."""
        
        _real: pyarray
        _imag: pyarray
        _data: pyarray
        _size: tuple[int, ...]
        _strides: list[int]
        size: tuple[int, ...]


def mlarray(obj: ArrayLike):
    """Convert an array-like object into a MATLAB array object."""
    arr = np.asarray(obj)
    arr_t = arr.T
    is_complex = arr.dtype.kind == "c"
    if is_complex:
        if arr.dtype == np.complex64:
            typecode = "f"
        elif arr.dtype == np.complex128:
            typecode = "d"
        else:
            raise TypeError(f"Unsupported complex type: {arr.dtype!r}.")
    else:
        typecode = PYARRAY_TYPE_MAP[arr_t.dtype]
    
    mlarr: "MLArray" = DTYPE_MAP[arr.dtype](is_complex=is_complex)
    
    mlarr._size = arr_t.shape
    mlarr._strides = np.cumprod((1,) + arr.shape[:-1]).tolist()
    if is_complex:
        mlarr._real = pyarray(typecode)
        mlarr._imag = pyarray(typecode)
        mlarr._real.frombytes(arr_t.real.tobytes())
        mlarr._imag.frombytes(arr_t.imag.tobytes())
    else:
        mlarr._data = pyarray(typecode)
        mlarr._data.frombytes(arr_t.tobytes())
    return mlarr

def mlarray_to_numpy(ml: "MLArray"):
    """Convert MATLAB array object into a numpy array."""
    
    if hasattr(ml, "_imag"):
        dtype = DTYPE_MAP_INV[type(ml)]
        real = np.asarray(ml._real, dtype=dtype)
        imag = np.asarray(ml._imag, dtype=dtype)
        arr = real + 1j * imag
    else:
        dtype = DTYPE_MAP_INV[type(ml)]
        arr = np.asarray(ml._data, dtype=dtype)
    return arr.reshape(ml.size[::-1]).T