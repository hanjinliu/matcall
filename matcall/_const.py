from ._matlab import (
    ml_double,
    ml_single,
    ml_complex64,
    ml_complex128,
    ml_uint8,
    ml_int8,
    ml_uint16,
    ml_int16, 
    ml_uint32,
    ml_int32,
    ml_uint64,
    ml_int64,
    ml_bool
)
import numpy as np

# These types does not need conversion.
BASIC_TYPES = (float, int, str, bool)

# Conversion from numpy.dtype to type of MATLAB matrix.
DTYPE_MAP = {
    np.dtype("int8"): ml_int8, 
    np.dtype("int16"): ml_int16,
    np.dtype("int32"): ml_int32, 
    np.dtype("int64"): ml_int64,
    np.dtype("float16"): ml_single,
    np.dtype("float32"): ml_single, 
    np.dtype("float64"): ml_double,
    np.dtype("complex64"): ml_complex64,
    np.dtype("complex128"): ml_complex128,
    np.dtype("uint8"): ml_uint8,
    np.dtype("uint16"): ml_uint16,
    np.dtype("uint32"): ml_uint32,
    np.dtype("uint64"): ml_uint64,
    np.dtype("bool"): ml_bool,
}

DTYPE_MAP_INV = {
    ml_int8: np.int8, 
    ml_int16: np.int16,
    ml_int32: np.int32, 
    ml_int64: np.int64,
    ml_single: np.float32, 
    ml_double: np.float64,
    ml_uint8: np.uint8,
    ml_uint16: np.uint16,
    ml_uint32: np.uint32,
    ml_uint64: np.uint64,
    ml_bool: np.bool_,
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
MATLAB_ARRAYS = (ml_double, ml_single, ml_uint8, ml_int8, ml_uint16, ml_int16, 
                 ml_uint32, ml_int32, ml_uint64, ml_int64, ml_bool)


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