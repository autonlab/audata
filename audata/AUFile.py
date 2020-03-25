import os
import h5py as h5
from dateutil import parser
import datetime as dt
import tzlocal
import pandas as pd
import numpy as np

from . import __VERSION_LIST__, __DATA_VERSION__
from .utils import json2dict, dict2json
from .AUGroup import AUGroup
from .AUDataset import AUDataset

class AUFile:
    DateTimeFormat = '%Y-%m-%d %H:%M:%S.%f %Z'

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

    @time_reference.setter
    def time_reference(self, new_ref):
        # If it's a date/time string, that's fine, but try to parse it first to make sure
        # the format is always consistent.
        if isinstance(new_ref, str):
            new_ref = parser.parse(new_ref)

        # Now only accept datetime objects.
        if isinstance(new_ref, dt.datetime):
            # We need a timezone. If none is given, assume it's local time.
            if new_ref.tzinfo is None:
                new_ref = tzlocal.get_localzone().localize(new_ref)
            self._time_reference = new_ref
            new_ref_str = new_ref.strftime(AUFile.DateTimeFormat)

            data = self.data
            data['time']['origin'] = new_ref_str
            self._f['.meta'].attrs['data'] = dict2json(data)

    @classmethod
    def new(cls, filename, overwrite=False, time_reference='now',
            title=None, author=None, organization=None):
        if os.path.exists(filename) and not overwrite:
            raise Exception('File "{}" already exists!'.format(filename))

        if time_reference == 'now':
            time_reference = dt.datetime.now(tz=tzlocal.get_localzone())

        f = h5.File(filename, 'w')
        f.create_group('.meta')
        f['.meta'].attrs['audata'] = dict2json({
            'version': [int(x) for x in __VERSION_LIST__],
            'data_version': __DATA_VERSION__
        })
        f['.meta'].attrs['data'] = dict2json({
            'title': title,
            'author': author,
            'organization': organization,
            'time': {
                'origin': time_reference.strftime(AUFile.DateTimeFormat),
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
        return json2dict(self._f['.meta'].attrs['audata'])

    @property
    def data(self):
        return json2dict(self._f['.meta'].attrs['data'])

    @classmethod
    def open(cls, filename, create=False, readonly=True):
        if not os.path.exists(filename):
            if create: return cls.new(filename)
            else: raise Exception(f'File not found: {filename}')

        c = cls()
        c._f = h5.File(filename, 'r' if readonly else 'a')
        c._filename = filename
        c._time_reference = parser.parse(c.data['time']['origin'])
        return c

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
