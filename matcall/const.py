from matlab import (double, single, uint8, int8, uint16, int16, 
                    uint32, int32, uint64, int64, logical)
import numpy as np
# These types does not need conversion.
BASIC_TYPES = (float, int, str, bool)

# Conversion from numpy.dtype to type of MATLAB matrix.
NUMPY_TO_MLARRAY = {np.dtype("int8"): int8, 
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
                    np.dtype("bool"): logical
                    }

# Types of MATLAB matrix.
MATLAB_ARRAYS = (double, single, uint8, int8, uint16, int16, 
                 uint32, int32, uint64, int64, logical)


SPECIAL_METHODS = {"plus": "__add__;__radd__",
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