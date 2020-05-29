import os
import h5py as h5
from dateutil import parser
import datetime as dt
import tzlocal
import pandas as pd
import numpy as np

from audata import __VERSION_LIST__, __DATA_VERSION__
from audata.utils import json2dict, dict2json
from audata.group import Group

class File(Group):
    DateTimeFormat = '%Y-%m-%d %H:%M:%S.%f %Z'

    def __init__(self, file, time_reference=None, return_datetimes=True):
        if not isinstance(file, h5.File):
            raise Exception(f'Invalid file type: {type(file)}')

        self._time_reference = time_reference
        self.return_datetimes = return_datetimes
        super().__init__(file)

    def __del__(self):
        if self is not None:
            self.close()

    @property
    def time_reference(self):
        return self._time_reference

    @time_reference.setter
    def time_reference(self, new_ref):
        if not self.valid:
            raise Exception('Attempting to use uninitialized File!')

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
            new_ref_str = new_ref.strftime(File.DateTimeFormat)

            data = self.meta_data
            data['time']['origin'] = new_ref_str
            self._h5['.meta'].attrs['data'] = dict2json(data)

    @classmethod
    def new(cls, filename, overwrite=False, time_reference='now',
            title=None, author=None, organization=None, return_datetimes=True, **kwargs):
        if os.path.exists(filename) and not overwrite:
            raise Exception('File "{}" already exists!'.format(filename))

        if time_reference == 'now':
            time_reference = dt.datetime.now(tz=tzlocal.get_localzone())

        f = h5.File(filename, 'w', **kwargs)
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
                'origin': time_reference.strftime(File.DateTimeFormat),
                'units': 'seconds'
            }
        })
        c = cls(f, time_reference=time_reference, return_datetimes=return_datetimes)
        return c

    @classmethod
    def open(cls, filename, create=False, readonly=True, return_datetimes=True):
        if not os.path.exists(filename):
            if create: return cls.new(filename)
            else: raise Exception(f'File not found: {filename}')

        f = h5.File(filename, 'r' if readonly else 'a')
        c = cls(f, return_datetimes=return_datetimes)
        c._time_reference = parser.parse(c.meta_data['time']['origin'])
        return c

    def close(self):
        if self._h5 is not None:
            self._h5.close()
            self.clear()

    def flush(self):
        if self._h5 is not None:
            self._h5.flush()
        else:
            raise Exception('No file opened!')

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
