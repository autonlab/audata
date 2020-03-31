import pandas as pd
import numpy as np
import h5py as h5
import datetime as dt
import jsbeautifier as jsb
import json

from numpy.lib.recfunctions import drop_fields


def df_from_audata(rec, meta, time_ref=None, string_ref=None, idx=slice(-1), datetimes=True):
    df = pd.DataFrame(data=rec)
    for col in meta['columns']:
        m = meta['columns'][col]
        if m['type'] == 'string':
            if string_ref is None:
                raise Exception('Cannot read strings without reference!')
            df[col] = string_ref[col][idx]
        elif m['type'] == 'factor':
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
    strings = {}
    for col in cols:
        m = {}
        d = df[col].dtype

        if d == h5.string_dtype():
            strings[col] = df[col].values
            del df[col]
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
    rec = df.to_records(index=False)
    return meta, strings, rec

def audata_from_arr(arr, time_cols=set(), timedelta_cols=set()):
    cols = arr.dtype.names
    cols_to_drop = []
    columns = {}
    strings = {}
    for col in cols:
        m = {}
        d = arr.dtype[col]

        if col in time_cols:
            # Assume time columns are already in seconds relative to the time reference.
            m['type'] = 'time'
            if d.kind != 'f':
                arr[col] = arr[col].astype('f8')
        elif col in timedelta_cols:
            # Assume time delta columns are already in seconds.
            m['type'] = 'timedelta'
            if d.kind != 'f':
                arr[col] = arr[col].astype('f8')
        elif d == h5.string_dtype():
            strings[col] = arr[col]
            cols_to_drop.append(col)
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
    if len(cols_to_drop) > 0:
        arr = drop_fields(arr, cols_to_drop)
    return meta, strings, arr

def json2dict(json_str):
    if not isinstance(json_str, str):
        raise Exception(f'Expecting string, found {type(json_str)}')
    return json.loads(json_str)

def dict2json(json_dict, format=True):
    if not isinstance(json_dict, dict):
        raise Exception(f'Expecting dictionary, found {type(json_dict)}')
    json_str = json.dumps(json_dict)
    return jsb.beautify(json_str) if format else json_str
