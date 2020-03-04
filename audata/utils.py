import pandas as pd
import numpy as np
import h5py as h5


def df_from_audata(rec, meta, time_ref=None, string_ref=None):
    df = pd.DataFrame(data=rec)
    for col in meta['columns']:
        m = meta['columns'][col]
        if m['type'] == 'string':
            if string_ref is None:
                raise Exception('Cannot read strings without reference!')
            df[col] = string_ref[col]
        elif m['type'] == 'factor':
            df[col] = pd.Categorical.from_codes(df[col].values, m['levels'])
        elif m['type'] == 'time':
            if time_ref is None:
                raise Exception('Cannot read timestamps without reference!')
            df[col] = np.datetime64(time_ref) + np.timedelta64(1, 's')*df[col].values
        elif m['type'] == 'timedelta':
            df[col] = np.timedelta64(1, 's')*df[col].values
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
