from matcall import translate
from pathlib import Path
import pytest

f = translate(Path(__file__).parent / "mfiles" / "identity.m")

@pytest.mark.parametrize("obj", [1, 1.0, True, "abc", [1, 2]])
def test_basic_types(obj):
    out = f(obj)
    assert out == obj

def test_struct():
    out = f({"a": 0, "b": [1, 2, 3]})
    repr(out)
    assert out.a == 0
    assert out.b == [1, 2, 3]

