from __future__ import annotations
import matlab.engine as eng
from matlab.engine import MatlabExecutionError
import numpy as np
import os
import re
import glob
from .const import BASIC_TYPES, DTYPE_MAP, MATLAB_ARRAYS, SPECIAL_METHODS
from .struct import MatStruct

ENGINE = eng.start_matlab()

from matlab import object as MatObject


class MatCaller:
    __all_methods__ = ["addpath", "translate", "eval"]
    
    def __init__(self):
        if "MATLABPATH" in os.environ.keys():
            root = os.environ["MATLABPATH"]
            ENGINE.addpath(root)
        
    def addpath(self, path:str, recursive:bool=False):
        """
        Add path to MATLAB engine.

        Parameters
        ----------
        dirpath : str
            The directory path to add.
        recursive : bool, optional
            If directories that contain ".m" file will be recursively added.
            By default False.

        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        
        if recursive:
            paths = glob.glob(f"{path}{os.sep}**{os.sep}", recursive=True)
            for path in paths:
                filelist = os.listdir(path)
                for file in filelist:
                    if file.endswith(".m"):
                        path = os.path.split(path)[0]
                        ENGINE.addpath(path)
                        break
        else:
            ENGINE.addpath(path)
                    
        return None
    
    def translate(self, funcname:str, nargout:int=-1, import_as=None, recursive=False):
        """
        Make MATLAB function without conversion between python object and MATLAB object.
        This is the simplest way to run MATLAB function. This function also suppors
        lambda function.

        Parameters
        ----------
        funcname : str
            The name of MATLAB function, or the absolute path to ".m" file.
        nargout : int, optional
            Number of output. Some functions are overloaded, therefore without nargout 
            they will throw error. By default -1.
        import_as : str or None, optional
            The methodname used in Python. In case the function's name conflicts with 
            the member functions. By default None. 
        recursive : bool, optional
            Passed to addpath() if funcname was an absolute path.

        Returns
        -------
        MatFunction object
        """
        if os.path.exists(funcname) and funcname.endswith(".m"):
            dirpath = os.path.dirname(funcname)
            funcname = os.path.splitext(os.path.basename(funcname))[0]
            self.addpath(dirpath, recursive=recursive)
        
        func = MatFunction(funcname, nargout=nargout)
        
        if import_as is None:
            import_as = funcname
            
        if import_as in self.__all_methods__:
            raise ValueError(f"Cannot overload MatCaller member function: {import_as}")
        
        if import_as.startswith("__") and import_as.endswith("__"):
            raise ValueError("Avoid names that start and end with '__'.")
        
        import_as.startswith("@") or setattr(self, import_as, func)
        
        return func
    

    def eval(self, matlab_input:str, nargout:int=-1):
        """
        Easily run a MATLAB-type input. Since the keyword argument "nargout" must be manually 
        assigned when using matlab.enging, it is troublesome for a interface. This function 
        enables automatic determination of nargout. 
        
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
    
    def __getattr__(self, key:str):
        try:
            out = to_pyobj(ENGINE.workspace[key])
        except MatlabExecutionError:
            try:
                out = self.translate(key)
            except Exception:
                raise AttributeError(f"Could not resolve attribute {key!r}.")
        return out
    
    def __setattr__(self, key:str, value):
        if not isinstance(value, MatFunction):
            ENGINE.workspace[key] = to_matobj(value)
        super().__setattr__(key, value)
        

class MatFunction:
    """
    Run MATLAB function without conversion between python object and MATLAB object.
    This class can also be used for class constructor. This is the simplest way to 
    run MATLAB function if no need for directly using MATLAB objects.
    """
    def __init__(self, name:str, nargout:int=-1):
        """
        Parameters
        ----------
        name : str or matlab.object of function_handle
            The name of function used in MATLAB
        nargout : int, optional
            The number of output. Some functions are overloaded, therefore without nargout
            they may throw error. By default -1.
        """
        # determine fhandle and name
        if isinstance(name, str):
            if name.startswith("@"):
                # lambda function
                self.fhandle = ENGINE.eval(name, nargout=1) 
            else:
                # symbolic function
                if not hasattr(ENGINE, name):
                    raise NameError(f"Unrecognized function: {name}")
                self.fhandle = ENGINE.eval("@" + name, nargout=1)
            self.name = name
            
        elif isinstance(name, MatObject):
            # function handle
            self.fhandle = name
            self.name = ENGINE.func2str(name)
            
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
    
    @property
    def __doc__(self):
        # docstring
        doc = ENGINE.evalc(f"help {self.name}")
        return _remove_html(doc)
    
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
        return f"MatClass<{self.__class__._real_name}> object at {hex(id(self))}"
    
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


def define_property(key):
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
       str    ->  char
       list   ->  cell
      tuple   ->  cell
       dict   -> struct (make sure all the keys are string)
    MatStruct -> struct
     ndarray  -> matrix
     
    """
    if isinstance(pyobj, np.ndarray):
        listobj = pyobj.tolist()
        matobj = DTYPE_MAP[pyobj.dtype](listobj)
    elif isinstance(pyobj, (list, tuple)):
        matobj = [to_matobj(each) for each in pyobj]
    elif isinstance(pyobj, BASIC_TYPES):
        matobj = pyobj
    elif isinstance(pyobj, (dict, MatStruct)):
        matobj = {k:to_matobj(v) for k, v in pyobj.items()}
    elif isinstance(pyobj, MatFunction):
        matobj = pyobj.fhandle
    elif isinstance(pyobj, MatClass):
        matobj = pyobj._obj
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
       others    -> MatClass object (if possible)
    """
    # TODO: table <-> data frame?
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
        if (_out_py.shape[0] == 1):
            _out_py = _out_py[0]
        elif (_out_py.ndim == 2 and _out_py.shape[1] == 1):
            _out_py = _out_py[:, 0]
    elif isinstance(matobj, MatObject):
        _out_py = translate_obj(matobj)
    else:
        _out_py = matobj

    return _out_py

_HTML_PATTERN = re.compile(r"<[^>]*?>")

def _remove_html(s:str):
    _disps = s.split("\n")
    for i, line in enumerate(_disps):
        if '<a href="' in line and "</a>" in line:
            _disps[i] = _HTML_PATTERN.sub("", line)
    return "\n".join(_disps)


# IPython magic
try:
    from IPython.core.magic import register_line_cell_magic
    @register_line_cell_magic
    def matlab(line, cell=None):
        if cell is None:
            cell = line
        try:
            _disp = ENGINE.evalc(cell, nargout=1)
        except Exception as e:
            err_msg = str(e)
            if err_msg.startswith("Error: "):
                err_msg = err_msg[7:]
            print(f"{e.__class__.__name__}: {err_msg}")
        else:
            if not cell.endswith(";"):
                print(_remove_html(_disp))
                
except ImportError:
    pass