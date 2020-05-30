import numpy as np
import pandas as pd
import h5py as h5

from typing import Union, AbstractSet, Optional, Tuple, Any, Dict

from audata import _utils as utils
from audata.element import Element


class Dataset(Element):
    """
    Maps to an HDF5 dataset, maintaining the `audata` schema and facilitating translation of
    higher-level data types. Generally should not be instantiated directly.
    """
    def __init__(self,
            au_parent : Element,
            name : str):
        if not isinstance(au_parent, Element):
            raise Exception(f'Invalid parent: {type(au_parent)}')

        parent = au_parent._h5
        if not isinstance(parent, h5.Group):
            raise Exception(f'Invalid parent: {type(parent)}')

        if name not in parent or not isinstance(parent[name], h5.Dataset):
            raise Exception(f'Path {name} is not a dataset in {parent.file.filename}:{parent.name}')

        super().__init__(au_parent, name)

    @classmethod
    def new(cls,
            au_parent : Element,
            name : str,
            value : Union[h5.Dataset, np.ndarray, np.recarray, pd.DataFrame],
            overwrite : bool = False,
            **kwargs) -> 'Dataset':

        if not isinstance(au_parent, Element):
            raise Exception('Must send Element.')

        parent = au_parent._h5
        if not isinstance(parent, h5.Group):
            raise Exception(f'Invalid parent: {type(parent)}')

        if name in parent and not overwrite:
            raise Exception(f'{name} already exists.')

        # If given an HDF5 dataset or an Dataset, read in all of its data
        # (HDF5 dataset as a numpy ndarray, Dataset as a pandas DataFrame).
        if isinstance(value, (h5.Dataset, Dataset)):
            value = value[:]

        # Try to create a class now.

        if isinstance(value, (np.ndarray, np.recarray)):
            return cls.__new_from_array(au_parent, name, value, **kwargs)

        elif isinstance(value, pd.DataFrame):
            return cls.__new_from_dataframe(au_parent, name, value)

        else:
            raise Exception(f'Unsure how to convert type {type(value)}')

    @classmethod
    def __new_from_array(cls,
            au_parent : Element,
            name : str,
            arr : Union[np.ndarray, np.recarray],
            time_cols : AbstractSet[str] = {},
            timedelta_cols : AbstractSet[str] = {}) -> 'Dataset':

        # ATW: TODO: Less lame.
        if arr.dtype.names is None:
            return cls.__new_from_dataframe(au_parent, name, pd.DataFrame(data=arr))

        meta, recs = utils.audata_from_arr(arr, time_ref=au_parent.file.time_reference,
            time_cols=time_cols, timedelta_cols=timedelta_cols)
        au_parent._h5.create_dataset(
            name, chunks=True, maxshape=(None,),
            compression='gzip', shuffle=True, fletcher32=True, data=recs)
        au_parent._h5[name].attrs['.meta'] = utils.dict2json(meta)
        d = cls(au_parent, name)
        return d

    @classmethod
    def __new_from_dataframe(cls,
            au_parent : Element,
            name : str,
            df : pd.DataFrame,
            time_cols : AbstractSet[str] = {},
            timedelta_cols : AbstractSet[str] = {}) -> 'Dataset':

        meta, recs = utils.audata_from_df(df, time_ref=au_parent.file.time_reference,
            time_cols=time_cols, timedelta_cols=timedelta_cols)
        au_parent._h5.create_dataset(
            name, chunks=True, maxshape=(None,),
            compression='gzip', shuffle=True, fletcher32=True, data=recs)
        au_parent._h5[name].attrs['.meta'] = utils.dict2json(meta)
        d = cls(au_parent, name)
        return d

    def __getitem__(self, idx = slice(-1)) -> pd.DataFrame:
        return self.get(idx)

    def get(self,
            idx = slice(-1),
            raw : bool = False,
            datetimes : Optional[bool] = None) -> pd.DataFrame:

        rec = self._h5[idx]
        if raw: return rec
        if isinstance(rec, np.void):
            rec = np.array([rec], dtype=rec.dtype)
        meta = self.meta

        if datetimes is None:
            datetimes = self.file.return_datetimes
        df = utils.df_from_audata(rec, meta, self.file.time_reference, idx, datetimes)
        return df

    def append(self,
            data : Union[pd.DataFrame, np.recarray],
            direct : bool = False,
            time_cols : AbstractSet[str] = {},
            timedelta_cols : AbstractSet[str] = {}):
        arr = None
        if isinstance(data, np.recarray):
            arr = data
            if not direct:
                _, arr = utils.audata_from_arr(arr, time_ref=self.time_reference,
                    time_cols=time_cols, timedelta_cols=timedelta_cols)
        elif direct:
            raise ValueError(f'Data must be in a recarray already to use direct append! Instead {type(data)} was sent.')
        elif isinstance(data, pd.DataFrame):
            # TODO: This does not validate categorical levels. So keep them the same!
            _, arr = utils.audata_from_df(data, time_ref=self.time_reference,
                time_cols=time_cols, timedelta_cols=timedelta_cols)

        N_data = len(arr)
        self._h5.resize((self.nrow + N_data,))
        self._h5[-N_data:] = arr

    @property
    def ncol(self) -> int:
        return len(self._h5.dtype)

    @property
    def nrow(self) -> int:
        return len(self._h5)

    @property
    def columns(self) -> Dict[str, Any]:
        return self.meta['columns']

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.nrow(), self.ncol())

    def __repr__(self):
        def trunc(s, N=20):
            if isinstance(s, str):
                if len(s) > N:
                    return s[:(N-3)] + '...'
                else:
                    return s
            else:
                return f'{s}'

        lines = []
        ncol = self.ncol
        nrow = self.nrow
        lines.append(f'{self.name}: Dataset [{nrow} rows x {ncol} cols]')
        cols = self.columns
        for col in cols:
            c = cols[col]
            if c['type'] == 'integer':
                tstr = 'integer ({})'.format('signed' if c['signed'] else 'unsigned')
            elif c['type'] == 'factor':
                nlevels = len(c['levels'])
                lvls = ', '.join([trunc(lvl) for lvl in c['levels'][:min(3,nlevels)]])
                if nlevels > 3:
                    lvls += ', ...'
                tstr = f'factor with {nlevels} levels [{lvls}]'
            else:
                tstr = c['type']
            lines.append(f'  {col}: {tstr}')
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()
