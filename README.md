# matcall

![](img1.png)

This Python module makes it much easier to run MATLAB functions and use MATLAB classes in Python codes. You can do almost anything in Python as in MATLAB.

## Contents

Following included:

- `MatCaller`, which handles MATLAB.
- `MatFunction`, which dynamically defines a function in Python from MATLAB function (including constructor).
- `MatClass`, which dynamically defines a class in Python from MATLAB class.
- `MatStruct`, which makes MATLAB's `struct` like object.
- `%%matlab` magic command.

## Preparation

First launch MATLAB in Python and make an instance by `mat = MatCaller()`. **Make sure you have downloaded MATLAB engine API for Python correctly and added its path by such as sys.path.append**.

```python
from matcall import MatCaller
import numpy as np

mat = MatCaller()
```

To add paths to MATLAB engine, use `addpath` function. You can also recursively add directory paths that .m files are contained.

```python
mat.addpath("path/to/the/file")
mat.addpath("path/to/the/file", recursive=True)
```

## MATLAB to Python conversion table

|MATLAB|Python|
|:----:|:----:|
|`logical`|`bool`|
|matrix (1x1)|`int` or `float`|
|matrix (1xN)|1-dim `ndarray`|
|matrix (Mx1)|1-dim `ndarray`|
|matrix (MxN)|`ndarray`|
|`char`|`str`|
|`cell`|`list`|
|`struct`|`MatStruct`|
|`function_handle`|`MatFunction`|
|others|`MatClass`|

## Python to MATLAB conversion table

|Python|MATLAB|
|:----:|:----:|
|`bool`|`logical`|
|`int` or `float`|matrix (1x1)|
|`str`|`char`|
|`list` or `tuple`|`cell`|
|`dict` or `MatStruct`|`struct`|
|`ndarray`|matrix|
|`MatFunction`|`function_handle`|
|`MatClass`|corresponding object|

# Basic Usage

Run MATLAB as if in MATLAB console.

```python
%%matlab
data.time = 1:100;
data.signal = sin(data.time/5.2);
data.name = "wave";
data
```

```
data = 

struct with fields:

    time: [1x100 double]
    signal: [1x100 double]
    name: "wave"
```

MATLAB workspace is accessible via `MatCaller` object. MATLAB objects are automatically converted to Python objects:

```python
mat.data.name
```

```
'wave'
```

or vice versa:

```python
mat.x = 10
%matlab x
```

```
x =

  int64

   10
```



## Use MATLAB Functions

MATLAB functions can be translated to Python function by

```python
mMax = mat.translate("max")
mMax
```
```
MatFunction<max>
```
```python
mMax(np.array([3,6,4]))
```
```
[Out]
    [6, 2.0]
```
MATLAB lambda function is also supported.
```python
sq = mat.translate("@(t)t^2")
sq 
```
```
MatFunction<@(t)t^2>
```
```python
sq(10)
```
```
100
```

## Use MATLAB Classes, Properties and Methods

Translation of MATLAB class constructor is also possible. Here constructor (not the class itself!) is returned and Python class will be dynamically defined with it. Same object is sent to MATLAB workspace only when it's needed.

```python
mycls = mat.translation("MyClass")
obj = mycls(x1, ..., xn)
```

Setter and getter are also (mostly) defined so that you can deal with the properties in a very simple way.

```python
mplot = mat.translate("plot")
pl = mplot(x, y)    # A figure window is openned here.
pl.Color = "red"    # The line color is changed to red here.
```

Examples
--------

#### Solve ODE using MATLAB `ode45` function.

```python
xlim = np.array([0., 20.])
v0 = np.array([2.,0.]).T
vdp1 = mat.translate("vdp1")
ode45 = mat.translate("ode45")
result = ode45(vdp1, xlim, v0)
result
```
```
MatStruct with 6 fields:
    solver: ode45
    extdata: MatStruct object (3 fields)
        x: np.ndarray (60,)
        y: np.ndarray (2, 60)
    stats: MatStruct object (3 fields)
    idata: MatStruct object (2 fields)
```


#### Calculate derivative using symbolic variables.

```python
sym = mat.translate("sym")
diff = mat.translate("diff")
x = sym("x")
A = sym("A")
f = A * np.sin(x)**2
print(diff(f))
```
```
2*A*cos(x)*sin(x)
```