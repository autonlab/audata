import pandas as pd
import numpy as np
import h5py as h5
import datetime as dt
import jsbeautifier as jsb
import json

from numpy.lib.recfunctions import drop_fields


def df_from_audata(rec, meta, time_ref=None, idx=slice(-1), datetimes=True):
    df = pd.DataFrame(data=rec)
    for col in meta['columns']:
        m = meta['columns'][col]
        if m['type'] == 'factor':
            df[col] = pd.Categorical.from_codes(df[col].values, m['levels'])
        elif m['type'] == 'time':
            if time_ref is None:
                raise Exception('Cannot read timestamps without reference!')
            if datetimes:
                df[col] = time_ref + df[col].values * dt.timedelta(seconds=1)
            else:
                df[col] += time_ref.timestamp()
        elif m['type'] == 'timedelta':
            df[col] = df[col].values * dt.timedelta(seconds=1)
    return df

def audata_from_df(df, time_ref=None):
    cols = list(df)
    columns = {}
    dtype_map = {}
    for col in cols:
        m = {}
        d = df[col].dtype

        if d == h5.string_dtype():
            # String d-type has to be set explicitely or HDF5 won't accept it. Default to
            # variable-length strings, although in the future we might want to support fixed-
            # length strings which can be compressed (vlen strings are NOT compressed).
            dtype_map[col] = h5.string_dtype()
            m['type'] = 'string'
        elif d.name == 'category':
            m['type'] = 'factor'
            m['levels'] = list(df[col].cat.categories)
            m['ordered'] = df[col].cat.ordered
            df[col] = df[col].cat.codes
        elif d.kind in ['i', 'u']:
            m['type'] = 'integer'
            m['signed'] = d.kind == 'i'
        elif d.kind == 'M':
            if time_ref is None:
                raise(Exception('Cannot convert timestamps without time reference!'))

            m['type'] = 'time'
            df[col] = (df[col].dt.tz_convert(time_ref.tzinfo) - time_ref).dt.total_seconds()
        elif d.kind == 'm':
            m['type'] = 'timedelta'
            df[col] = df[col].dt.total_seconds()
        else:
            typenames = {
                'b': 'boolean',
                'f': 'real',
                'c': 'complex'
            }
            m['type'] = typenames[d.kind]
        columns[col] = m

    meta = {'columns': columns}
    rec = df.to_records(index=False, column_dtypes=dtype_map)
    return meta, rec

def audata_from_arr(arr, time_ref=None):
    # TODO: Factor types are not supported in this mode. Also not supported: non-string objects.
    cols = arr.dtype.names
    columns = {}
    for col in cols:
        m = {}
        d = arr.dtype[col]

        if d.kind == 'M':
            if time_ref is None:
                raise(Exception('Cannot convert timestamps without time reference!'))

            # Note: Since numpy datetime64 types are note timezone aware, we must assume the datetimes
            # use the same timezone.
            m['type'] = 'time'
            arr[col] = (arr[col] - np.datetime64(time_ref.replace(tzinfo=None))) / np.timedelta64(1, 's')
        elif d.kind == 'm':
            m['type'] = 'timedelta'
            arr[col] = arr[col] / np.timedelta64(1, 's')
        elif d == h5.string_dtype():
            if h5.check_vlen_dtype(d) != str:
                arr[col] = arr[col].astype(h5.string_dtype())
            m['type'] = 'string'
        elif d.kind in ['i', 'u']:
            m['type'] = 'integer'
            m['signed'] = d.kind == 'i'
        else:
            typenames = {
                'b': 'boolean',
                'f': 'real',
                'c': 'complex'
            }
            m['type'] = typenames[d.kind]
        columns[col] = m

    meta = {'columns': columns}
    return meta, arr

def json2dict(json_str):
    if not isinstance(json_str, str):
        raise Exception(f'Expecting string, found {type(json_str)}')
    return json.loads(json_str)

def dict2json(json_dict, format=True):
    if not isinstance(json_dict, dict):
        raise Exception(f'Expecting dictionary, found {type(json_dict)}')
    json_str = json.dumps(json_dict)
    return jsb.beautify(json_str) if format else json_str
