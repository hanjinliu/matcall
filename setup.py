from setuptools import setup

with open("matcall/__init__.py", encoding="utf-8") as f:
    for line in f:
        if (line.startswith("__version__")):
            VERSION = line.strip().split()[-1][1:-1]
            break
      
setup(name="matcall",
      version=VERSION,
      description="Use MATLAB functions and classes in Python.",
      author="Hanjin Liu",
      author_email="liuhanjin-sc@g.ecc.u-tokyo.ac.jp",
      license="GPLv2",
      packages=["matcall"],
      install_requires=[
            "numpy",
      ],
      python_requires=">=3.6|<3.9",
      )