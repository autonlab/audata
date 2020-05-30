from setuptools import setup, find_packages
import numpy as np
import os

from audata import __VERSION__

NAME = 'audata'
VERSION = __VERSION__


def read(fn):
    return open(os.path.join(os.path.dirname(__file__), fn)).read()


setup(
    name=NAME,
    version=VERSION,
    description='A python package for reading and writing data for AUView.',
    long_description=read('readme.md'),
    author='Anthony Wertz',
    author_email='awertz@cmu.edu',
    license='GNU LGPL 3',
    entry_points={
        'console_scripts': ['csv2audata=audata.bin.csv2audata:main']
    },
    install_requires=[
        'numpy',
        'pandas',
        'h5py',
        'jsbeautifier',
        'lorem',
        'tzlocal',
        'h5py'
    ],
    python_requires='>=3.8',
    include_dirs=[np.get_include()],
    packages=find_packages()
)
