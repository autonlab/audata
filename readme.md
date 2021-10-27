# Auton Universal Data

Welcome to the source code for Auton Universal Data (AUData). AUData is both a file schema and a toolset. This source repository contains the documentation of the file specification and a Python library for working with audata files.

## Documentation

Further documentation is available at [audata.readthedocs.io](https://audata.readthedocs.io/en/latest/)

## Installation

To install audata, simply use pip:

```
pip install audata
```

## Building

If you'd like to build from source code (e.g. for development purposes):

```
python setup.py bdist_wheel
pip install -U dist/*.whl
cd test
python write.py
```
