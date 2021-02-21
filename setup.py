from setuptools import setup

setup(name="matcall",
      version="1.2.5",
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