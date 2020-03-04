import os
import h5py as h5
import datetime as dt
import tzlocal
import json
import pandas as pd
import numpy as np

from . import __VERSION_LIST__, __DATA_VERSION__
from .AUGroup import AUGroup
from .AUDataset import AUDataset

class AUFile:
    def __init__(self):
        self._f = None
        self._filename = None
        self._time_reference = None

    def __del__(self):
        if self is not None:
            self.close()

    @property
    def time_reference(self):
        return self._time_reference

    @classmethod
    def new(cls, filename, overwrite=False, time_reference='now',
            title=None, author=None, organization=None):
        if os.path.exists(filename) and not overwrite:
            raise Exception('File "{}" already exists!'.format(filename))

        if time_reference == 'now':
            time_reference = dt.datetime.now(tzlocal.get_localzone())

        f = h5.File(filename, 'w')
        f.create_group('.meta')
        f['.meta'].attrs['audata'] = json.dumps({
            'version': [int(x) for x in __VERSION_LIST__],
            'data_version': __DATA_VERSION__
        })
        f['.meta'].attrs['data'] = json.dumps({
            'title': title,
            'author': author,
            'organization': organization,
            'time': {
                'origin': time_reference.strftime('%Y-%M-%d %H:%M:%S.%f %Z'),
                'units': 'seconds'
            }
        })
        c = cls()
        c._f = f
        c._filename = filename
        c._time_reference = time_reference
        return c

    @property
    def audata(self):
        return json.loads(self._f['.meta'].attrs['audata'])

    @property
    def data(self):
        return json.loads(self._f['.meta'].attrs['data'])

    @classmethod
    def open(cls, file_name, mode='r'):
        pass

    def __getitem__(self, key):
        if self._f is None:
            raise Exception('No file opened.')

        if key == '':
            return AUGroup(self, key)

        if key in self._f:
            if isinstance(self._f[key], h5.Dataset):
                return AUDataset(self, key)
            elif isinstance(self._f[key], h5.Group):
                return AUGroup(self, key)
            else:
                raise Exception('Unsure how to handle class: {}'.format(type(self._f[key])))
        else:
            return None

    def __setitem__(self, key, value):
        if self._f is None:
            raise Exception('No file opened.')

        if value is None:
            if key in self._f:
                del self._f[key]
        else:
            AUDataset.new(self, key, value, overwrite=True)

    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = None

    def __repr__(self):
        return self.__getitem__('').__repr__()

    def __str__(self):
        return self.__getitem__('').__str__()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

def mkdf(N=100):
    import lorem
    ref = dt.datetime.now(tzlocal.get_localzone())
    return pd.DataFrame(
        data={
            'time': [ref + dt.timedelta(seconds=x/250.0) for x in range(N)],
            'time2': [ref + dt.timedelta(seconds=x/250.0 + 0.5) for x in range(N)],
            'ints': list(range(N)),
            'floats': [i*1.1 for i in list(range(N))],
            'strings': [lorem.sentence() for x in range(N)],
            'factor': pd.Series([['Cat', 'Dog', 'Liger'][x % 3] for x in range(N)], dtype='category')
        }
    )
