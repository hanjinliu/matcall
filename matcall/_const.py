from matlab import (double, single, uint8, int8, uint16, int16, 
                    uint32, int32, uint64, int64, logical)
import numpy as np
from functools import partial

complex64 = partial(single, is_complex=True)
complex128 = partial(double, is_complex=True)

# These types does not need conversion.
BASIC_TYPES = (float, int, str, bool)

# Conversion from numpy.dtype to type of MATLAB matrix.
DTYPE_MAP = {
    np.dtype("int8"): int8, 
    np.dtype("int16"): int16,
    np.dtype("int32"): int32, 
    np.dtype("int64"): int64,
    np.dtype("float16"): single,
    np.dtype("float32"): single, 
    np.dtype("float64"): double,
    np.dtype("uint8"): uint8,
    np.dtype("uint16"): uint16,
    np.dtype("uint32"): uint32,
    np.dtype("uint64"): uint64,
    np.dtype("bool"): logical,
}

DTYPE_MAP_INV = {
    int8: np.int8, 
    int16: np.int16,
    int32: np.int32, 
    int64: np.int64,
    single: np.float32, 
    double: np.float64,
    uint8: np.uint8,
    uint16: np.uint16,
    uint32: np.uint32,
    uint64: np.uint64,
    logical: np.bool_,
}


PYARRAY_TYPE_MAP = {
    np.dtype("int8"): "b", 
    np.dtype("int16"): "h",
    np.dtype("int32"): "i", 
    np.dtype("int64"): "l",
    np.dtype("float16"): "f",
    np.dtype("float32"): "f", 
    np.dtype("float64"): "d",
    np.dtype("uint8"): "B",
    np.dtype("uint16"): "H",
    np.dtype("uint32"): "I",
    np.dtype("uint64"): "L",
    np.dtype("bool"): "B",
}

PYARRAY_TYPE_MAP_INV = {
    "b": np.int8, 
    "h": np.int16,
    "i": np.int32, 
    "l": np.int64,
    "f": np.float32, 
    "d": np.float64,
    "B": np.uint8,
    "H": np.uint16,
    "I": np.uint32,
    "L": np.uint64,
}

# Types of MATLAB matrix.
MATLAB_ARRAYS = (double, single, uint8, int8, uint16, int16, 
                 uint32, int32, uint64, int64, logical)


SPECIAL_METHODS = {
    "plus": "__add__;__radd__",
    "minus": "__sub__;__rsub__",
    "times": "__mul__;__rmul__",
    "rdivide": "__truediv__",
    "uminus": "__neg__",
    "eq": "__eq__",
    "gt": "__gt__",
    "ge": "__ge__",
    "lt": "__lt__",
    "le": "__le__",
    "ne": "__ne__",
    "power": "__pow__",
    "char": "__str__",
    "double": "__float__;double",
    "and": "__and__",
    "or": "__or__",
    "not": "__not__"
}