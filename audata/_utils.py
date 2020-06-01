import pandas as pd
import numpy as np
import h5py as h5
import datetime as dt
import jsbeautifier as jsb
import json

from numpy.lib.recfunctions import drop_fields

from typing import Optional, Dict, Any, AbstractSet, Tuple, Union


def df_from_audata(rec,
                   meta: Dict[str, Any],
                   time_ref: Optional[dt.datetime] = None,
                   idx=slice(-1),
                   datetimes: bool = True) -> pd.DataFrame:

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


def audata_from_df(df: pd.DataFrame,
                   time_ref: Optional[dt.datetime] = None,
                   time_cols: AbstractSet[str] = {},
                   timedelta_cols: AbstractSet[str] = {}
                  ) -> Tuple[Dict[str, Any], np.recarray]:

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
                raise (Exception(
                    'Cannot convert timestamps without time reference!'))

            m['type'] = 'time'
            df[col] = (df[col].dt.tz_convert(time_ref.tzinfo) -
                       time_ref).dt.total_seconds()
        elif d.kind == 'm':
            m['type'] = 'timedelta'
            df[col] = df[col].dt.total_seconds()
        elif col in time_cols:
            # Assume offset from reference in appropriate units.
            m['type'] = 'time'
            dtype_map[col] = 'f8'
        elif col in timedelta_cols:
            # Assume delta in appropriate units.
            m['type'] = 'timedelta'
            dtype_map[col] = 'f8'
        else:
            typenames = {'b': 'boolean', 'f': 'real', 'c': 'complex'}
            m['type'] = typenames[d.kind]
        columns[col] = m

    meta = {'columns': columns}
    rec = df.to_records(index=False, column_dtypes=dtype_map)
    return meta, rec


def audata_from_arr(arr: Union[np.ndarray, np.recarray],
                    time_ref: Optional[dt.datetime] = None,
                    time_cols: AbstractSet[str] = {},
                    timedelta_cols: AbstractSet[str] = {}
                   ) -> Tuple[Dict[str, Any], np.recarray]:

    # TODO: Factor types are not supported in this mode. Also not supported: non-string objects.
    cols = arr.dtype.names
    columns = {}
    for col in cols:
        m = {}
        d = arr.dtype[col]

        if d.kind == 'M':
            if time_ref is None:
                raise (Exception(
                    'Cannot convert timestamps without time reference!'))

            # Note: Since numpy datetime64 types are note timezone aware, we must assume the datetimes
            # use the same timezone.
            m['type'] = 'time'
            arr[col] = (arr[col] - np.datetime64(
                time_ref.replace(tzinfo=None))) / np.timedelta64(1, 's')
        elif d.kind == 'm':
            m['type'] = 'timedelta'
            arr[col] = arr[col] / np.timedelta64(1, 's')
        elif d == h5.string_dtype():
            if h5.check_vlen_dtype(d) != str:
                arr[col] = arr[col].astype(h5.string_dtype())
            m['type'] = 'string'
        elif col in time_cols:
            # Assume offset from reference in appropriate units.
            m['type'] = 'time'
            if d.type != 'f':
                arr[col] = arr[col].astype('f8')
        elif col in timedelta_cols:
            # Assume delta in appropriate units.
            m['type'] = 'timedelta'
            if d.type != 'f':
                arr[col] = arr[col].astype('f8')
        elif d.kind in ['i', 'u']:
            m['type'] = 'integer'
            m['signed'] = d.kind == 'i'
        else:
            typenames = {'b': 'boolean', 'f': 'real', 'c': 'complex'}
            m['type'] = typenames[d.kind]
        columns[col] = m

    meta = {'columns': columns}
    return meta, arr


def json2dict(json_str: str) -> Dict[str, Any]:
    if not isinstance(json_str, str):
        raise Exception(f'Expecting string, found {type(json_str)}')
    return json.loads(json_str)


def dict2json(json_dict: Dict[str, Any], format: bool = True) -> str:
    if not isinstance(json_dict, dict):
        raise Exception(f'Expecting dictionary, found {type(json_dict)}')
    json_str = json.dumps(json_dict)
    return jsb.beautify(json_str) if format else json_str
