from __future__ import annotations
from functools import cached_property
import os
from pathlib import Path
from typing import overload, NewType
import warnings

_MATCALL_DIRECTORY = Path(__file__).parent
_INFO_PATH = _MATCALL_DIRECTORY / "matcall-info.txt"
if _INFO_PATH.exists():
    import sys
    with open(_INFO_PATH, mode="r") as f:
        s = f.read().strip()
    sys.path.append(s)

import matlab.engine as eng
from matlab.engine import MatlabExecutionError
import numpy as np
import pandas as pd
import glob
from ._const import BASIC_TYPES, DTYPE_MAP, MATLAB_ARRAYS, SPECIAL_METHODS
from .struct import MatStruct
from ._utils import remove_html

ENGINE = eng.start_matlab()

from matlab import object as MatObject

ENGINE.addpath(str(_MATCALL_DIRECTORY))

if "MATLABPATH" in os.environ.keys():
    root = os.environ["MATLABPATH"]
    ENGINE.addpath(root)

class MatlabWorkspace:
    def __getattr__(self, key: str):
        try:
            out = to_pyobj(ENGINE.workspace[key])
        except MatlabExecutionError:
            try:
                out = translate(key)
            except Exception:
                raise AttributeError(f"Could not resolve attribute {key!r}.")
        return out
    
    def __setattr__(self, key: str, value):
        ENGINE.workspace[key] = to_matobj(value)
    
    __getitem__ = __getattr__
    __setitem__ = __setattr__

workspace = MatlabWorkspace()

def addpath(path: str, recursive: bool = False):
    """
    Add path to MATLAB engine.

    Parameters
    ----------
    path : str
        The directory path to add.
    recursive : bool, optional
        If directories that contain ".m" file will be recursively added.
        By default False.

    """
    path = str(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    
    if recursive:
        paths = glob.glob(f"{path}{os.sep}**{os.sep}", recursive=True)
        for path in paths:
            filelist = os.listdir(path)
            for file in filelist:
                if file.endswith(".m"):
                    path = os.path.dirname(path)
                    ENGINE.addpath(path)
                    break
    else:
        ENGINE.addpath(path)
                
    return None

FunctionName = NewType("FunctionName", str)

@overload
def translate(
    mpath: str | Path | bytes,
    nargout: int = -1,
    recursive: bool = False,
) -> MatFunction:
    ...

@overload
def translate(
    mpath: FunctionName,
    nargout: int = -1,
) -> MatFunction:
    ...

def translate(funcname, nargout: int = -1, recursive: bool = False,
):
    """
    Make MATLAB function without conversion between python object and MATLAB object.
    This is the simplest way to run MATLAB function. This function also suppors
    lambda function.

    Parameters
    ----------
    funcname : str or path-like
        The name of MATLAB function, or the absolute path to ".m" file.
    nargout : int, optional
        Number of output. Some functions are overloaded, therefore without nargout 
        they will throw error. By default -1.
    recursive : bool, optional
        Passed to addpath() if funcname was an absolute path.

    Returns
    -------
    MatFunction object
    """
    funcname = str(funcname)
    if os.path.exists(funcname) and funcname.endswith(".m"):
        dirpath = os.path.dirname(funcname)
        funcname = os.path.splitext(os.path.basename(funcname))[0]
        addpath(dirpath, recursive=recursive)
    else:
        if recursive:
            warnings.warn(
                "'recursive=True' does nothing if function name is given",
                UserWarning,
            )
    
    return MatFunction(funcname, nargout=nargout)


def eval(matlab_input: str, nargout: int = -1):
    """
    Easily run a MATLAB-type input. Since the keyword argument "nargout" must be
    manually assigned when using matlab.enging, it is troublesome for a interface. 
    This function enables automatic determination of nargout. 
    
    Usage:
    >>> main_instance.eval("arr = [0, 1, 2, 3, 4]")
    >>> main_instance.eval("sqrt(arr)")
    """
    if matlab_input == "":
        return None
    
    if nargout < 0:
        if ";" in matlab_input:
            nargout = 0
        elif "=" in matlab_input:
            if "==" in matlab_input:
                nargout = 1
            else:
                nargout = 0
        elif "@" in matlab_input:
            nargout = 1
        elif "(" in matlab_input:
            funcname, _ = matlab_input.split("(", 1)
            nargout = int(ENGINE.nargout(funcname, nargout=1))
            if nargout < 0:
                nargout = 1
        elif " " in matlab_input:
            nargout = 0
        else:
            nargout = 1
    
    _out = ENGINE.eval(matlab_input, nargout=nargout)
    _out_py = to_pyobj(_out)
    return _out_py

class MatFunction:
    """
    MATLAB function object.
    
    This object can run MATLAB function without conversion between python object
    and MATLAB object. This class can also be used for class constructor. This is
    the simplest way to run MATLAB function if no need for directly using MATLAB 
    objects.
    """
    
    def __init__(self, name: str, nargout: int = -1):
        """
        Parameters
        ----------
        name : str or matlab.object of function_handle
            The name of function used in MATLAB
        nargout : int, default is -1
            The number of output. Some functions are overloaded, therefore without 
            ``nargout`` they may throw error.
        """
        # determine fhandle and name
        if isinstance(name, str):
            if name.startswith("@"):
                # lambda function
                self.fhandle = ENGINE.eval(name, nargout=1)
                self.__name__ = name[1:]
            else:
                # symbolic function
                if not hasattr(ENGINE, name):
                    raise NameError(f"Unrecognized function: {name}")
                self.fhandle = ENGINE.eval("@" + name, nargout=1)
                self.__name__ = name
            self.name = name
            
        elif isinstance(name, MatObject):
            # function handle
            self.fhandle = name
            self.name: str = ENGINE.func2str(name)
            self.__name__ = self.name.lstrip("@")
            
        else:
            raise TypeError("'name' must be str or matlab.object of function_handle")
        
        # determine nargout
        if nargout < 0:
            if self.name.startswith("@"):
                nargout = 1
            else:
                nargout = int(ENGINE.nargout(name, nargout=1))
                if nargout < 0:
                    nargout = 1
                    
        self.nargout = nargout
        self.__module__ = "matcall"
    
    def __repr__(self):
        return f"MatFunction<{self.name}>"
    
    def __call__(self, *argin):        
        # make matlab inputs
        inputlist = map(to_matobj, argin)
                
        # run function
        outputlist = ENGINE.feval(self.fhandle, *inputlist, nargout=self.nargout)
        
        # process output
        pyobj = to_pyobj(outputlist)
        
        return pyobj
    
    @cached_property
    def __doc__(self):
        # docstring
        doc = ENGINE.evalc(f"help {self.name}")
        return remove_html(doc)
    
    # TODO: __signature__
        

_MATLAB_CLASS: dict[str, type] = {}

class MatClass:
    """
    This class makes matlab.object compatible to Python object.
    
    Because matlab.object is just a handle of MATLAB class instance, it is troublesome to
    access properties or methods:
    - For properties, they must be accessed by eng.eval("obj.prop").
    - For methods, inputs must be converted into MATLAB workspace every time and the function
      must be called by e.g. eng.feval("func", obj, x1, ..., xn, nargout=...)
    MatClass enables descriptions like 'obj.prop' or 'obj.func(x1, ..., xn)'.
    To avoid wasting memory with unused objects, matlab.object is sent to MATLAB workspace
    by NewClass._send() only when it is needed.
    """
    _real_name: str
    
    def __init__(self, obj):
        self._obj = obj
    
    def __repr__(self):
        return f"<{self.__class__._real_name}> object at {hex(id(self))}"
    
    def _send(self):
        """
        When Python needs to access matlab.object, the object is sent to MATLAB workspace by
        this function. To avoid collision, the number of object in MATLAB is counted in
        ThisClass._record.

        Returns
        -------
        str
            The symbol used in MATLAB.
        """
        if hasattr(self, "_objname"):
            return self._objname
        clsname = self.__class__.__name__
        objname = f"{clsname}{hex(id(self))}"
        self._objname = objname
        ENGINE.workspace[self._objname] = to_matobj(self._obj)
        
        return objname
    
    def __hash__(self) -> int:
        return hash(self._objname)


def define_property(key: str):
    """
    Dynamically define setter and getter for property.
    """
    def getter(self: MatClass):
        if hasattr(self, "get"):
            return to_pyobj(self.get(key))
        else:
            objname = self._send()
            value = ENGINE.eval(f"{objname}.{key}", nargout=1)
            return to_pyobj(value)
    
    def setter(self: MatClass, value):
        objname = self._send()
        if hasattr(self, "set"):
            self.set(key, value)
        elif isinstance(value, bool):
            ENGINE.eval(f"{objname}.{key}={str(value).lower()};", nargout=0)   
        elif isinstance(value, (int, float)):
            ENGINE.eval(f"{objname}.{key}={value};", nargout=0)
        elif isinstance(value, str):
            ENGINE.eval(f"{objname}.{key}='{value}';", nargout=0)
        elif isinstance(value, np.ndarray) and value.ndim == 1:
            ENGINE.eval(f"{objname}.{key}={list(value)};", nargout=0)
        else:
            raise AttributeError("Complicated property setting is not "\
                f"supported in {self.__class__._real_name}.")
        
    return property(getter, setter)

def define_method(key):
    """
    Dynamically define setter and getter for methods.
    """
    def getter(self):
        def func(*argin, nargout=1):
            inputlist = map(to_matobj, argin)
            outputlist = ENGINE.feval(key, self._obj, *inputlist, nargout=nargout)
            pyobj = to_pyobj(outputlist)
            return pyobj
            
        return func
    
    def setter(self, value):
        raise AttributeError("Cannot set value to methods.")
    
    return property(getter, setter)

    
def translate_obj(obj):
    """
    Dynamically define a class based on MATLAB class.

    Parameters
    ----------
    obj : matlab.object
        The object handle from which new class to be defined will make reference.

    Return
    -------
    object of newly defined class, or MatFunction.
    """        
    _real_name = ENGINE.feval("class", obj, nargout=1)
    
    if _real_name == "function_handle":
        return MatFunction(obj)
    elif _real_name == "table":
        _dict: dict = ENGINE.table2struct(obj, "ToScalar", True)
        _dict = {k: to_pyobj(v) for k, v in _dict.items()}
        try:
            import pandas as pd
            return pd.DataFrame(_dict)
        except ImportError:
            return _dict
    
    newclass_name = "_".join(_real_name.split("."))
    
    if newclass_name in _MATLAB_CLASS:
        newclass = _MATLAB_CLASS[newclass_name]
    else:
        # Prepare class
        attrs = dict(_record = 0, _real_name=_real_name)
        newclass = type(newclass_name, (MatClass,), attrs)
        _MATLAB_CLASS[newclass_name] = newclass
        
        # define setter and getter
        for prop_name in ENGINE.properties(_real_name, nargout=1):
            setattr(newclass, prop_name, define_property(prop_name))
        
        # for special methods such as 'plus', they are converted to the corresponding
        # Python one such as '__add__'.
        for method_name in ENGINE.methods(_real_name, nargout=1):
            method_name_in_python = SPECIAL_METHODS.get(method_name, method_name)
            for n in method_name_in_python.split(";"):
                setattr(newclass, n, define_method(method_name))
        
    new = newclass(obj)
    
    return new       
    
    
def to_matobj(pyobj):
    """
    Convert python object to MATLAB object.
    
      python     MATLAB
    ------------------
       bool   -> logical
       int    -> matrix (1x1)
      float   -> matrix (1x1)
    str, Path ->  char
       list   ->  cell
      tuple   ->  cell
       dict   -> struct (make sure all the keys are string)
    MatStruct -> struct
     ndarray  -> matrix
    DataFrame ->  table
     
    """
    if isinstance(pyobj, np.ndarray):
        listobj = pyobj.tolist()
        matobj = DTYPE_MAP[pyobj.dtype](listobj)
    elif isinstance(pyobj, (list, tuple)):
        matobj = [to_matobj(each) for each in pyobj]
    elif isinstance(pyobj, BASIC_TYPES):
        matobj = pyobj
    elif isinstance(pyobj, (dict, MatStruct)):
        matobj = {k: to_matobj(v) for k, v in pyobj.items()}
    elif isinstance(pyobj, MatFunction):
        matobj = pyobj.fhandle
    elif isinstance(pyobj, MatClass):
        matobj = pyobj._obj
    elif isinstance(pyobj, pd.DataFrame):
        _dict = {k: DTYPE_MAP[v.dtype](np.asarray(v).reshape(-1, 1).tolist()) 
                 for k, v in pyobj.to_dict("series").items()}
        matobj = ENGINE.struct2table(_dict)
    elif isinstance(pyobj, Path):
        matobj = str(pyobj)
    elif isinstance(pyobj, MatObject):
        matobj = pyobj
    else:
        raise TypeError(f"Cannot convert {type(pyobj)} to MATLAB object.")
    
    return matobj

def to_pyobj(matobj):
    """
    Convert MATLAB object in MATLAB workspace to python object recursively.
    
       MATLAB       python
    ------------------------
      logical    ->  bool
    matrix (1x1) -> float
    matrix (1xN) -> 1-dim ndarray (row vector)
    matrix (Mx1) -> 1-dim ndarray (row vector)
    matrix (MxN) -> ndarray
        char     ->  str
        cell     ->  list (1xN or Nx1)
       struct    ->  MatStruct object
       table     -> DataFrame
       others    -> MatClass object (if possible)
    """
    if matobj is None:
        _out_py = matobj
    elif isinstance(matobj, BASIC_TYPES):
        _out_py = matobj
    elif isinstance(matobj, (list, tuple)):
        _out_py = [to_pyobj(each) for each in matobj]
    elif isinstance(matobj, dict):
        _out_py = MatStruct({k: to_pyobj(v) for k, v in matobj.items()})
    elif matobj.size == (1, 1) and isinstance(matobj[0][0], BASIC_TYPES):
        _out_py = matobj[0][0]
    elif isinstance(matobj, MATLAB_ARRAYS):
        _out_py = np.array(matobj)
        if _out_py.shape[0] == 1:
            _out_py = _out_py[0]
        elif _out_py.ndim == 2 and _out_py.shape[1] == 1:
            _out_py = _out_py[:, 0]
    elif isinstance(matobj, MatObject):
        _out_py = translate_obj(matobj)
    else:
        _out_py = matobj

    return _out_py
