from matcall import translate
from pathlib import Path
import numpy as np
import pytest

MFILES = Path(__file__).parent / "mfiles"
DTYPES = [
    np.int8, np.int16, np.int32, np.float32, np.float64, np.complex64, 
    np.complex128, np.bool_, np.uint8, np.uint16, np.uint32,
]
f = translate(Path(__file__).parent / "mfiles" / "identity.m")

@pytest.mark.parametrize("dtype", DTYPES)
def test_dtype_consistency(dtype):
    arr = np.zeros(2, dtype=dtype)
    assert f(arr).dtype == dtype
