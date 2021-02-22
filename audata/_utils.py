"""Helper utilities."""
import datetime as dt
import json
from typing import Optional, Dict, Any, AbstractSet, Tuple, Union

import pandas as pd
import numpy as np
import h5py as h5
import jsbeautifier as jsb


def df_from_audata(rec,
                   columns: Dict[str, Any],
                   time_ref: Optional[dt.datetime] = None,
                   datetimes: bool = True) -> pd.DataFrame:
    """Create a pandas DataFrame from an audata Dataset."""

    data = pd.DataFrame(data=rec)
    for col in columns:

        col_meta = columns[col]

        if col_meta['type'] == 'factor':
            data[col] = pd.Categorical.from_codes(data[col].values, col_meta['levels'])

        elif col_meta['type'] == 'time':

            if time_ref is None:
                raise Exception('Cannot read timestamps without reference!')

            # If datetimes were requested, convert the time column into a seconds time delta and add it to the time ref
            if datetimes:
                data[col] = time_ref + pd.to_timedelta(data[col], unit='s')

            else:
                data[col] += time_ref.timestamp()
        elif col_meta['type'] == 'timedelta':
            data[col] = data[col].values * dt.timedelta(seconds=1)
    return data


def audata_from_df(data: pd.DataFrame,
                   time_ref: Optional[dt.datetime] = None,
                   time_cols: Optional[AbstractSet[str]] = None,
                   timedelta_cols: Optional[AbstractSet[str]] = None
                  ) -> Tuple[Dict[str, Any], np.recarray]:
    """Create the recarray and meta from a DataFrame to be stored to the audata file."""

    if time_cols is None:
        time_cols = set({})
    if timedelta_cols is None:
        time_cols = set({})
    cols = list(data)
    columns = {}
    dtype_map = {}
    for col in cols:
        col_meta = {}
        col_dtype = data[col].dtype

        if col_dtype == h5.string_dtype():
            # String d-type has to be set explicitely or HDF5 won't accept it. Default to
            # variable-length strings, although in the future we might want to support fixed-
            # length strings which can be compressed (vlen strings are NOT compressed).
            dtype_map[col] = h5.string_dtype()
            col_meta['type'] = 'string'
        elif col_dtype.name == 'category':
            col_meta['type'] = 'factor'
            col_meta['levels'] = list(data[col].cat.categories)
            col_meta['ordered'] = data[col].cat.ordered
            data[col] = data[col].cat.codes
        elif col_dtype.kind in ['i', 'u']:
            col_meta['type'] = 'integer'
            col_meta['signed'] = col_dtype.kind == 'i'
        elif col_dtype.kind == 'M':
            if time_ref is None:
                raise (Exception('Cannot convert timestamps without time reference!'))

            col_meta['type'] = 'time'
            data[col] = (data[col].dt.tz_convert(time_ref.tzinfo) -
                         time_ref).dt.total_seconds()
        elif col_dtype.kind == 'm':
            col_meta['type'] = 'timedelta'
            data[col] = data[col].dt.total_seconds()
        elif col in time_cols:
            # Assume offset from reference in appropriate units.
            col_meta['type'] = 'time'
            dtype_map[col] = 'f8'
        elif col in timedelta_cols:
            # Assume delta in appropriate units.
            col_meta['type'] = 'timedelta'
            dtype_map[col] = 'f8'
        else:
            typenames = {'b': 'boolean', 'f': 'real', 'c': 'complex'}
            col_meta['type'] = typenames[col_dtype.kind]
        columns[col] = col_meta

    meta = {'columns': columns}
    rec = data.to_records(index=False, column_dtypes=dtype_map)
    return meta, rec


def audata_from_arr(arr: Union[np.ndarray, np.recarray],
                    time_ref: Optional[dt.datetime] = None,
                    time_cols: Optional[AbstractSet[str]] = None,
                    timedelta_cols: Optional[AbstractSet[str]] = None
                   ) -> Tuple[Dict[str, Any], np.recarray]:
    """Create the recarray and meta from a recarray or ndarray to be stored to the audata file."""

    # Issue 4: Factor types are not supported in this mode. Also not supported: non-string objects.
    if time_cols is None:
        time_cols = set({})
    if timedelta_cols is None:
        time_cols = set({})
    cols = arr.dtype.names
    columns = {}
    for col in cols:
        col_meta = {}
        col_dtype = arr.dtype[col]

        if col_dtype.kind == 'M':
            if time_ref is None:
                raise (Exception('Cannot convert timestamps without time reference!'))

            # Note: Since numpy datetime64 types are not timezone aware, we must
            # assume the datetimes use the same timezone.
            col_meta['type'] = 'time'
            arr[col] = (arr[col] - np.datetime64(time_ref.replace(tzinfo=None))) / np.timedelta64(1, 's')
        elif col_dtype.kind == 'm':
            col_meta['type'] = 'timedelta'
            arr[col] = arr[col] / np.timedelta64(1, 's')
        elif col_dtype == h5.string_dtype():
            if h5.check_vlen_dtype(col_dtype) != str:
                arr[col] = arr[col].astype(h5.string_dtype())
            col_meta['type'] = 'string'
        elif col in time_cols:
            # Assume offset from reference in appropriate units.
            col_meta['type'] = 'time'
            if col_dtype.type != 'f':
                arr[col] = arr[col].astype('f8')
        elif col in timedelta_cols:
            # Assume delta in appropriate units.
            col_meta['type'] = 'timedelta'
            if col_dtype.type != 'f':
                arr[col] = arr[col].astype('f8')
        elif col_dtype.kind in ['i', 'u']:
            col_meta['type'] = 'integer'
            col_meta['signed'] = col_dtype.kind == 'i'
        else:
            typenames = {'b': 'boolean', 'f': 'real', 'c': 'complex'}
            col_meta['type'] = typenames[col_dtype.kind]
        columns[col] = col_meta

    meta = {'columns': columns}
    return meta, arr

# Makes a best effort to determine column type based only on dtype. Returns a
# dict containing keys 'type' and, if applicable, 'signed'.
# TODO(gus): At somep point, it would be nice to merge this with how
# audata_from_df() and audata_from_arr() determine column type.
def get_coltype_from_dtype_only(dtype) -> Dict[str, Any]:

    if dtype.kind == 'M':
        return { 'type': 'time' }
    elif dtype.kind == 'm':
        return { 'type': 'timedelta' }
    elif dtype == h5.string_dtype():
        return { 'type': 'string' }
    elif dtype.kind == 'i':
        return {
            'type': 'integer',
            'signed': False
        }
    elif dtype.kind == 'u':
        return {
            'type': 'integer',
            'signed': True
        }
    elif dtype.kind == 'b':
        return { 'type': 'boolean' }
    elif dtype.kind == 'f':
        return {'type': 'real' }
    elif dtype.kind == 'c':
        return {'type': 'complex' }
    else:
        raise Exception('Unrecognized column type.')

def json2dict(json_str: str) -> Dict[str, Any]:
    """Convert JSON string to python dictionary."""
    return json.loads(json_str)


def dict2json(json_dict: Dict[str, Any], beautify: bool = True) -> str:
    """Convert JSON-compatible python dictionary to beautified JSON string."""
    if not isinstance(json_dict, dict):
        raise Exception(f'Expecting dictionary, found {type(json_dict)}')

    if beautify:
        return jsb.beautify(json.dumps(json_dict))
    else:
        return json.dumps(json_dict)
