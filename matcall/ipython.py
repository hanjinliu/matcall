from __future__ import annotations
from IPython.core.magic import register_line_cell_magic
import os
import tempfile
from .core import ENGINE
from ._utils import remove_html

_MATCALL_DIRECTORY = os.path.dirname(__file__)

@register_line_cell_magic
def matlab(line: str, cell: str | None = None):
    if cell is None:
        cell = line
        
    if cell.startswith("function "):
        # Function cannot be defined in this way. We have to make a temporary ".m" file.
        pref = cell.split("(")[0]
        if "=" in pref:
            pref = pref.split("=")[1]
        funcname = pref.strip()
        with tempfile.NamedTemporaryFile(
            dir=_MATCALL_DIRECTORY, suffix=".m", delete=False
        ) as tf:
            filepath = tf.name
            with open(filepath, mode="w+") as f:
                f.write(cell)
        
        funcpath = os.path.join(_MATCALL_DIRECTORY, funcname + ".m")
        if os.path.exists(funcpath):
            os.remove(funcpath)
        os.rename(filepath, funcpath)
        
    else:
        try:
            _disp = ENGINE.evalc(cell, nargout=1)
        except Exception as e:
            err_msg = str(e)
            if err_msg.startswith("Error: "):
                err_msg = err_msg[7:]
            print(f"{e.__class__.__name__}: {err_msg}")
        else:
            if not cell.endswith(";"):
                print(remove_html(_disp))

    