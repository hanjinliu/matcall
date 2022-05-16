import numpy as np
from ._const import *

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
    
    def __init__(self, dict_=None):
        dict_ = dict_ or dict()
        super().__setattr__("_all", [])
        for k, v in dict_.items():
            setattr(self, k, v)
    
    def __getitem__(self, key):
        """
        To make MatStruct almost the same as dict.
        """
        if key in self._all:
            return getattr(self, key)
        else:
            raise KeyError(key)
    
    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        self._all.append(key)
    
    def __len__(self):
        return len(self._all)
    
    def __iter__(self):
        return zip(self._all, (getattr(self, k) for k in self._all))
    
    def __repr__(self):
        out = f"MatStruct with {len(self)} fields:\n"
        longest = max([len(s) for s in self._all])
        for k, v in self:
            out += " " * (longest - len(k) + 4)
            if isinstance(v, BASIC_TYPES):
                description = v
            elif isinstance(v, np.ndarray):
                description = f"np.ndarray {v.shape}"
            elif isinstance(v, self.__class__):
                description = f"MatStruct object ({len(v)} fields)"
            elif isinstance(v, list):
                description = f"list (length {len(v)})"
            else:
                description = type(v)
            out += f"{k}: {description}\n"
            
        return out