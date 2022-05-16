from matcall import addpath, translate
from pathlib import Path
import numpy as np
import pandas as pd

MFILES = Path(__file__).parent / "mfiles"

def test_path():
    f = translate(MFILES/"test_array.m")
    assert f.__name__ == "test_array"

def test_function_name():
    addpath(MFILES/"test_array.m")
    f = translate("test_array")
    assert f.__name__ == "test_array"

def test_array():
    _test_array = translate(MFILES/"test_array.m")
    out = _test_array(np.arange(10), 3.0)
    assert type(out) is np.ndarray
    assert np.allclose(out, np.arange(10) * 3.0)
    
def test_table():
    _test_table = translate(MFILES/"test_table.m")
    out = _test_table({"col_0": [0, 1, 2, 3], "col_1": [True, False, True, True]})
    assert type(out) is pd.DataFrame
    assert all(out.columns == ["col_0", "col_1"])
    assert np.all(out["col_0"] == [0, 1, 2, 3])
    assert np.all(out["col_1"] == [True, False, True, True])
