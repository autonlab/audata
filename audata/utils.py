import pandas as pd
import numpy as np
import h5py as h5
import jsbeautifier as jsb
import json


def df_from_audata(rec, meta, time_ref=None, string_ref=None, idx=slice(-1)):
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
            df[col] = np.datetime64(time_ref) + df[col].values * 10**9 * np.timedelta64(1, 'ns')
        elif m['type'] == 'timedelta':
            df[col] = df[col].values * 10**9 * np.timedelta64(1, 'ns')
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

def json2dict(json_str):
    if not isinstance(json_str, str):
        raise Exception(f'Expecting string, found {type(json_str)}')
    return json.loads(json_str)

def dict2json(json_dict, format=True):
    if not isinstance(json_dict, dict):
        raise Exception(f'Expecting dictionary, found {type(json_dict)}')
    json_str = json.dumps(json_dict)
    return jsb.beautify(json_str) if format else json_str
