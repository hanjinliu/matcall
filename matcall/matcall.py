from matlab import (double, single, uint8, int8, uint16, int16, 
                    uint32, int32, uint64, int64, logical)
import matlab.engine as eng
import numpy as np
import os
import glob

# MATLAB engine used after matcall is imported.
ENGINE = eng.start_matlab()

from matlab import object as MatObject

# These types does not need conversion.
BASIC_TYPES = (float, int, str, bool)

# Conversion from numpy.dtype to type of MATLAB matrix.
NtoM = {np.dtype("int8"): int8, 
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


class MatCaller:
    """
    Function-wrapping class that makes better MATLAB-Python interface.
    No need to manually determine the number of outputs.

    Usage
    -----
    
    First launch MATLAB in Python and make an instance. 
    
    >>> from matcall import MatCaller
    >>> mat = MatCaller()
    
    To add a path "C:/Users/..." to MATLAB engine, use addpath() function.
    
    >>> mat.addpath("C:/Users/...")
    
    or recursively search for ".m" file and add the path.
    
    >>> mat.addpath("C:/Users/...", child = True)
    
    For correspondence of MATLAB/Python object, see the docstring in to_pyobj() and to_matobj().
    Remember that python list is converted to cell object in MATLAB. Use np.ndarray for MATLAB
    vectors and matices.
    
    You can run MATLAB using console() and obtain one object as return value.
    
    >>> out = mat.console()
    (MATLAB) In >>> a = 1:5;
    (MATLAB) In >>> b = sqrt(a);
    (MATLAB) In >>> return b
    >>> out
    array([1.        , 1.41421356, 1.73205081, 2.        , 2.23606798])

    MATLAB function can be translated to Python function by
    
    >>> mMax = mat.translate("max")
    >>> mMax
    MatFunction<max>
    >>> mMax(np.array([3,6,4]))
    [6, 2.0]
    
    Translation of MATLAB class constructor is also possible. Here constructor (not the class
    itself!) is returned and Python class will be dynamically defined with it. Same object
    is sent to MATLAB workspace only when it's needed.
    
    >>> mycls = mat.translation("MyClass")
    >>> obj = mycls(x1, ..., xn)
    >>> obj
    MatClass<MyClass>
    >>> out = obj.method1() # obj is sent to MATLAB workspace here.

    Setting/getting method is also (mostly) defined so that you can deal with the properties
    in a very simple way.
    
    >>> mplot = mat.translate("plot")
    >>> pl = mplot(x, y)    # A figure window is openned here.
    >>> pl.Color = "red"    # The line color is changed to red here.
    
    A struct object in MATLAB is translated to dict object in Python by default. However, it
    is a little bit troublesome to access the contents of dict, compared to MATLAB struct (at
    least you need to type double quotation every time). Thus, here in matcall a MatStruct
    object is returned instead.
    
    >>> out = mat.console()
    (MATLAB) In >>> st.a = [1, 2, 3];
    (MATLAB) In >>> st.b = -1;
    (MATLAB) In >>> st.c = {"This", "is", "cell"};
    (MATLAB) In >>> return st
    >>> out
    MatStruct with 3 fields:
        a: np.ndarray (3,)
        b: -1.0
        c: list (length 3)
    >>> out.c
    ['This', 'is', 'cell']
    
    """

    __all_methods__ = ["addpath", "console", "translate", "eval", "workspace"]
    
    def __init__(self):
        if ("MATLABPATH" in os.environ.keys()):
            root = os.environ["MATLABPATH"]
            ENGINE.addpath(root)
        
    def addpath(self, dirpath:str, child:bool=False):
        """
        Add path to MATLAB engine.

        Parameters
        ----------
        dirpath : str
            The directory path to add.
        child : bool, optional
            If directories that contain ".m" file will be recursively added.
            By default False.

        """
        if (not os.path.exists(dirpath)):
            raise FileNotFoundError(f"Path '{dirpath}' does not exist.")
        
        ENGINE.addpath(dirpath)
        
        if child:
            paths = glob.glob(f"{dirpath}{os.sep}**{os.sep}", recursive=True)
            for path in paths:
                filelist = os.listdir(path)
                for file in filelist:
                    if file.endswith(".m"):
                        ENGINE.addpath(path)
                        break
                    
        return None
    
    def console(self):
        """
        Start MATLAB console.
        Each line is sent to MatCaller.eval().
        Use 'return XX' to return the value of XX to Python.
        Use 'exit' to just exit from the console.
        """
        import re
        html_tag = re.compile(r"<[^>]*?>")
        
        _in = ""
        _out = None
        while True:
            _in = input("(MATLAB) In >>> ")
            if (_in == "return"):
                break
            elif (_in.startswith("return ")):
                val = _in.strip(";").split(" ")
                if (len(val) > 2):
                    print("Syntax Error.")
                else:
                    ifexist = ENGINE.exist(val[1], nargout=1)
                    if (ifexist):
                        obj = ENGINE.workspace[val[1]]
                        _out = to_pyobj(obj)
                        break
                    else:
                        print(f"NameError: '{val[1]}' does not exists in the MATLAB workspace.")
                    
            elif (_in == "exit"):
                _out = None
                break
            else:
                try:
                    _disp = ENGINE.evalc(_in, nargout=1)
                except Exception as e:
                    err_msg = str(e)
                    if (err_msg.startswith("Error: ")):
                        err_msg = err_msg[7:]
                    print(f"{e.__class__.__name__}: {err_msg}")
                else:
                    if (not _in.endswith(";")):
                        _disps = _disp.split("\n")
                        for i, line in enumerate(_disps):
                            if('<a href="' in line and "</a>" in line):
                                _disps[i] = html_tag.sub("", line)
                        print("\n".join(_disps))
                        

        return _out
    
    
    def translate(self, funcname:str, nargout:int=-1, import_as=None, child=False):
        """
        Make MATLAB function without conversion between python object and MATLAB object.
        This is the simplest way to run MATLAB function if no need for directly using
        MATLAB objects.

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
        child : bool, optional
            Passed to addpath() if funcname was an absolute path.

        Returns
        -------
        MatFunction object
        """
        if (os.path.exists(funcname) and funcname.endswith(".m")):
            dirpath = os.path.dirname(funcname)
            funcname = os.path.splitext(os.path.basename(funcname))[0]
            self.addpath(dirpath, child=child)
        
        func = MatFunction(funcname, nargout=nargout)
        
        if (import_as is None):
            import_as = funcname
            
        if (import_as in self.__all_methods__):
            raise ValueError(f"Cannot overload MatCaller member function: {import_as}")
        
        if (import_as.startswith("__")):
            raise ValueError("Avoid names that start with '__'.")
            
        setattr(self, import_as, func)
        
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
        if (matlab_input == ""):
            return None
        
        if (nargout < 0):
            if (";" in matlab_input):
                nargout = 0
            elif ("=" in matlab_input):
                nargout = 0
            elif("@" in matlab_input):
                nargout = 1
            elif ("(" in matlab_input):
                funcname, _ = matlab_input.split("(", 1)
                nargout = int(ENGINE.nargout(funcname, nargout=1))
                if (nargout < 0):
                    nargout = 1
            elif (" " in matlab_input):
                nargout = 0
            else:
                nargout = 1
        
        _out = ENGINE.eval(matlab_input, nargout=nargout)
        _out_py = to_pyobj(_out)
        return _out_py    

    def workspace(self):
        """
        Open the MATLAB workspace window.
        """
        ENGINE.feval("workspace", nargout=0)
        return None
    

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
        name : str
            The name of function used in MATLAB
        caller : MatCaller object
            MatCaller object whose enging will be used.
        nargout : int, optional
            The number of output. Some functions are overloaded, therefore without nargout
            they may throw error. By default -1.

        Raises
        ------
        NameError
            If function 'name' doesn't exist in MATLAB.
        """        
        
        self.name = name
        
        if (not hasattr(ENGINE, name)):
            raise NameError(f"Unrecognized function: {name}")
        
        if (nargout < 0):
            nargout = int(ENGINE.nargout(self.name, nargout=1))
            if (nargout < 0):
                nargout = 1
                
        self.nargout = nargout
    
    def __repr__(self):
        return f"MatFunction<{self.name}>"
    
    def __call__(self, *argin):        
        # make matlab inputs
        inputlist = map(to_matobj, argin)
                
        # run function
        outputlist = ENGINE.feval(self.name, *inputlist, nargout=self.nargout)
        
        # process output
        pyobj = to_pyobj(outputlist)
        
        return pyobj
    
    def doc(self):
        """
        Open a window and search for the docstring of the function.
        """
        ENGINE.doc(self.name, nargout=0)
        return None
    
    def as_handle(self):
        """
        Convert to a MATLAB function handle.

        Returns
        -------
        matlab.object
            function handle of self.
        """
        return ENGINE.eval(f"@{self.name}", nargout=1)


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
    _classes = {} # name -> class
    
    def __init__(self, obj):
        self._obj = obj
    
    def __repr__(self):
        return f"MatClass<{self.__class__._real_name}>"
        
    def __getattribute__(self, key:str):
        """
        Get attribute method that enables getting MATLAB properties and methods.
        """
        if (key.startswith("_")):
            return super().__getattribute__(key)
        
        elif (key in self._properties):
            objname = self._send()
            value = ENGINE.eval(f"{objname}.{key}", nargout=1)
            return to_pyobj(value)
        
        elif (key in self._methods):
            # Re-define a method. See MatFunction.__call__().
            def func(*argin, nargout=1):
                inputlist = map(to_matobj, argin)
                outputlist = ENGINE.feval(key, self._obj, *inputlist, nargout=nargout)
                pyobj = to_pyobj(outputlist)
                return pyobj
            
            return func
        
        else:
            raise AttributeError(f"Unknown property or method: {key}")
    
    def __setattr__(self, key: str, value):
        if (key.startswith("_")):
            super().__setattr__(key, value)
            
        elif (key in self.__class__._properties):
            objname = self._send()
            if ("set" in self.__class__._methods):
                self.set(key, value)
            elif (isinstance(value, bool)):
                ENGINE.eval(f"{objname}.{key}={str(value).lower()};", nargout=0)   
            elif (isinstance(value, (int, float))):
                ENGINE.eval(f"{objname}.{key}={value};", nargout=0)
            elif (isinstance(value, str)):
                ENGINE.eval(f"{objname}.{key}='{value}';", nargout=0)
            elif (isinstance(value, np.ndarray) and value.ndim == 1):
                ENGINE.eval(f"{objname}.{key}={list(value)};", nargout=0)
            else:
                raise AttributeError(f"Complicated property setting is not "\
                    "supported in {self.__class__._real_name}.")
        else:
            raise ValueError("Invalid attribution setting.")
    
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
        if (hasattr(self, "_objname")):
            return self._objname
        clsname = self.__class__.__name__
        objname = f"{clsname}_No{self.__class__._record}"
        self._objname = objname
        ENGINE.workspace[self._objname] = to_matobj(self._obj)
        self.__class__._record += 1
        return objname


class MatStruct:
    """
    Class for MATLAB-struct like object.
    This class does not need connection to MATLAB.
    e.g.)
    >>> d = {"field1": 1, "field2": True, "arr": np.arange(5)}
    >>> st = MatStruct(d)
    >>> st
    MatStruct with 3 fields:
        field1: 1
        field2: True
           arr: np.ndarray (5,)
    >>> st.arr
    array([0, 1, 2, 3, 4])
    
    Attribute '_all' and '_longest' does not conflict with other field names because symbols
    cannot start with underscore in MATLAB.
    """
    __all_methods__ = ("as_dict", "keys", "items")
    
    def __init__(self, dict_):
        super().__setattr__("_longest", 0)
        super().__setattr__("_all", [])
        super().__setattr__("_n_field", 0)
        for k, v in dict_.items():
            setattr(self, k, v)
            self._all.append(k)
    
    def __getitem__(self, key):
        if (key in self._all):
            return getattr(self, key)
        else:
            raise KeyError(key)
    
    def __setattr__(self, key, value):
        if (key in self.__all_methods__):
            raise ValueError(f"Cannot set field {key} because it "\
                              "conflicts with existing member function.")
        super().__setattr__(key, value)
        super().__setattr__("_longest", max(self._longest, len(key)))
        super().__setattr__("_n_field", self._n_field + 1)
    
    def __repr__(self):
        out = f"\nMatStruct with {self._n_field} fields:\n"
        for k, v in self.items():
            out += " " * (self._longest - len(k) + 4)
            if (isinstance(v, BASIC_TYPES)):
                description = v
            elif (isinstance(v, np.ndarray)):
                description = f"np.ndarray {v.shape}"
            elif (isinstance(v, self.__class__)):
                description = f"MatStruct object ({v._n_field} fields)"
            elif (isinstance(v, list)):
                description = f"list (length {len(v)})"
            else:
                description = type(v)
            out += f"{k}: {description}\n"
            
        return out

    def as_dict(self):
        return {k: getattr(self, k) for k in self._all}

    def keys(self):
        return self._all
    
    def items(self):
        for k in self._all:
            yield k, getattr(self, k)

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
    
    if (_real_name == "function_handle"):
        return MatFunction(ENGINE.func2str(obj, nargout=1))
    
    if ("." in _real_name):
        newclass_name = "_".join(_real_name.split("."))
    else:
        newclass_name = _real_name
    
    if (newclass_name in MatClass._classes):
        newclass = MatClass._classes[newclass_name]
    else:
        # Prepare class methods
        attrs = dict(
            _record = 0,
            _real_name = _real_name,
            _properties = ENGINE.properties(_real_name, nargout=1),
            _methods = ENGINE.methods(_real_name, nargout=1)
        )
        newclass = type(newclass_name, (MatClass,), attrs)
        MatClass._classes[newclass_name] = newclass
        
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
    if (isinstance(pyobj, np.ndarray)):
        listobj = pyobj.tolist()
        matobj = NtoM[pyobj.dtype](listobj)
    elif (isinstance(pyobj, (list, tuple))):
        matobj = [to_matobj(each) for each in pyobj]
    elif (isinstance(pyobj, BASIC_TYPES)):
        matobj = pyobj
    elif (isinstance(pyobj, (dict, MatStruct))):
        matobj = {k:to_matobj(v) for k, v in pyobj.items()}
    elif (isinstance(pyobj, MatFunction)):
        matobj = pyobj.as_handle()
    elif (isinstance(pyobj, MatClass)):
        matobj = pyobj._obj
    elif (isinstance(pyobj, MatObject)):
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
    
    if (matobj is None):
        _out_py = matobj
    elif (isinstance(matobj, BASIC_TYPES)):
        _out_py = matobj
    elif (isinstance(matobj, (list, tuple))):
        _out_py = [to_pyobj(each) for each in matobj]
    elif (isinstance(matobj, dict)):
        _out_py = MatStruct({k: to_pyobj(v) for k, v in matobj.items()})
    elif (matobj.size == (1, 1) and isinstance(matobj[0][0], BASIC_TYPES)):
        _out_py = matobj[0][0]
    elif (isinstance(matobj, MATLAB_ARRAYS)):
        _out_py = np.array(matobj)
        if (_out_py.shape[0] == 1):
            _out_py = _out_py[0]
        elif (_out_py.ndim == 2 and _out_py.shape[1] == 1):
            _out_py = _out_py[:, 0]
    elif (isinstance(matobj, MatObject)):
        _out_py = translate_obj(matobj)
    else:
        _out_py = matobj

    return _out_py
