import matlab.engine as eng
import numpy as np
import os
import glob
from .const import *
from .struct import MatStruct

ENGINE = eng.start_matlab()

from matlab import object as MatObject


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

    __all_methods__ = ["addpath", "console", "translate", "eval", "workspace", 
                       "added_path", "console_hist", "eng"]
    
    def __init__(self):
        if ("MATLABPATH" in os.environ.keys()):
            root = os.environ["MATLABPATH"]
            ENGINE.addpath(root)
        self.added_path = [root]
        self.console_hist = []
        self.eng = ENGINE
        
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
        
        if child:
            paths = glob.glob(f"{dirpath}{os.sep}**{os.sep}", recursive=True)
            for path in paths:
                filelist = os.listdir(path)
                for file in filelist:
                    if file.endswith(".m"):
                        path = os.path.split(path)[0]
                        ENGINE.addpath(path)
                        self.added_path.append(path)
                        break
        else:
            ENGINE.addpath(dirpath)
            self.added_path.append(dirpath)
                    
        return None
    
    def console(self, inputs=[]):
        """
        Start MATLAB console.
        Each line is sent to MatCaller.eval().
        Use 'return XX' to return the value of XX to Python.
        Use 'exit' to just exit from the console.
        
        Parameters
        ----------
        inputs : slice, list or tuple
            Input lines that are run before user inputs. If it is slice, then it will
            passed to console history.
        """
        import re
        html_tag = re.compile(r"<[^>]*?>")
        if (isinstance(inputs, slice)):
            inputs = self.console_hist[inputs]
        elif (isinstance(inputs, (list, tuple))):
            inputs = list(inputs)
        else:
            raise TypeError("'inputs' must be slice, list or tuple")
        
        _out = None
        while True:
            if (inputs):
                _in = inputs.pop(0)
                print("(MATLAB) In >>> " + "\n            >>> ".join(_in.split("\n")))
            else:
                stack = 0
                _ins = []
                while True:
                    if (stack == 0):
                        prefix = "(MATLAB) In >>> "
                    else:
                        prefix = "            >>> "
                    _in0 = input(prefix).rstrip()
                    if (_in0.startswith(("for ", "function ", "if ", "while ", "switch ", "try "))):
                        stack += 1
                    elif (_in0.lstrip() == "end" and stack > 0):
                        stack -= 1
                    
                    _ins.append(_in0.rstrip())
                    
                    if (stack <= 0):
                        break
                    
                _in = "\n".join(_ins)
                
            self.console_hist.append(_in)
            
            if (_in == "return"):
                break
            elif (_in.startswith("return ")):
                val = _in[7:].strip(";")
                ifexist = ENGINE.exist(val, nargout=1)
                if (ifexist):
                    obj = ENGINE.workspace[val]
                    _out = to_pyobj(obj)
                    break
                else:
                    try:
                        _out = self.eval(val)
                        break
                    except:
                        print(f"Error: Invalid return value.")
                        self.console_hist.pop()
                    
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
                    self.console_hist.pop()
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
        
        if (import_as.startswith("__") and import_as.endswith("__")):
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
        if (matlab_input == ""):
            return None
        
        if (nargout < 0):
            if (";" in matlab_input):
                nargout = 0
            elif ("=" in matlab_input):
                if ("==" in matlab_input):
                    nargout = 1
                else:
                    nargout = 0
            elif ("@" in matlab_input):
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
        name : str or matlab.object of function_handle
            The name of function used in MATLAB
        nargout : int, optional
            The number of output. Some functions are overloaded, therefore without nargout
            they may throw error. By default -1.

        Attributes
        ----------
        fhandle : matlab.object
            function_handle object of MATLAB engine.
        name : str
            the function name.
        nargout : int
            The number of output.
            
        Raises
        ------
        NameError
            If function 'name' doesn't exist in MATLAB. Lambda function will not raise
            NameError.
        """
        # determine fhandle and name
        if (isinstance(name, str)):
            if (name.startswith("@")):
                # lambda function
                self.fhandle = ENGINE.eval(name, nargout=1) 
            else:
                # symbolic function
                if (not hasattr(ENGINE, name)):
                    raise NameError(f"Unrecognized function: {name}")
                self.fhandle = ENGINE.eval("@" + name, nargout=1)
            self.name = name
            
        elif (isinstance(name, MatObject)):
            # function handle
            self.fhandle = name
            self.name = ENGINE.func2str(name)
            
        else:
            raise TypeError("'name' must be str or matlab.object of function_handle")
        
        # determine nargout
        if (nargout < 0):
            if (self.name.startswith("@")):
                nargout = 1
            else:
                nargout = int(ENGINE.nargout(name, nargout=1))
                if (nargout < 0):
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
    
    def doc(self):
        """
        Open a window and search for the docstring of the function.
        """
        ENGINE.doc(self.name, nargout=0)
        return None


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


def setget_property(key):
    """
    Dynamically define setter and getter for property.
    """
    def getter(self):
        if (hasattr(self, "get")):
            return to_pyobj(self.get(key))
        else:
            objname = self._send()
            value = ENGINE.eval(f"{objname}.{key}", nargout=1)
            return to_pyobj(value)
    
    def setter(self, value):
        objname = self._send()
        if (hasattr(self, "set")):
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
            raise AttributeError("Complicated property setting is not "\
                f"supported in {self.__class__._real_name}.")
        
    return property(getter, setter)

def setget_methods(key):
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
    
    if (_real_name == "function_handle"):
        return MatFunction(obj)
    
    newclass_name = "_".join(_real_name.split("."))
    
    if (newclass_name in MatClass._classes):
        newclass = MatClass._classes[newclass_name]
    else:
        # Prepare class
        attrs = dict(_record = 0, _real_name = _real_name)
        newclass = type(newclass_name, (MatClass,), attrs)
        MatClass._classes[newclass_name] = newclass
        
        # define setter and getter
        for prop_name in ENGINE.properties(_real_name, nargout=1):
            setattr(newclass, prop_name, setget_property(prop_name))
        
        # for special methods such as 'plus', they are converted to the corresponding
        # Python one such as '__add__'.
        for method_name in ENGINE.methods(_real_name, nargout=1):
            method_name_in_python = SPECIAL_METHODS.get(method_name, method_name)
            for n in method_name_in_python.split(";"):
                setattr(newclass, n, setget_methods(method_name))
        
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
        matobj = NUMPY_TO_MLARRAY[pyobj.dtype](listobj)
    elif (isinstance(pyobj, (list, tuple))):
        matobj = [to_matobj(each) for each in pyobj]
    elif (isinstance(pyobj, BASIC_TYPES)):
        matobj = pyobj
    elif (isinstance(pyobj, (dict, MatStruct))):
        matobj = {k:to_matobj(v) for k, v in pyobj.items()}
    elif (isinstance(pyobj, MatFunction)):
        matobj = pyobj.fhandle
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


# IPython magic
try:
    from IPython.core.magic import register_cell_magic
    @register_cell_magic
    def matlab(line, cell):
        import re
        html_tag = re.compile(r"<[^>]*?>")
        try:
            _disp = ENGINE.evalc(cell, nargout=1)
        except Exception as e:
            err_msg = str(e)
            if (err_msg.startswith("Error: ")):
                err_msg = err_msg[7:]
            print(f"{e.__class__.__name__}: {err_msg}")
        else:
            if (not cell.endswith(";")):
                _disps = _disp.split("\n")
                for i, line in enumerate(_disps):
                    if('<a href="' in line and "</a>" in line):
                        _disps[i] = html_tag.sub("", line)
                print("\n".join(_disps))
                
except ImportError:
    pass