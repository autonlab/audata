import numpy as np
import pandas as pd
import h5py as h5

from . import utils
from .AUElement import AUElement


class AUDataset(AUElement):
    def __init__(self, au_parent, name):
        if not isinstance(au_parent, AUElement):
            raise Exception(f'Invalid parent: {type(au_parent)}')

        parent = au_parent._h5
        if not isinstance(parent, h5.Group):
            raise Exception(f'Invalid parent: {type(parent)}')

        if name not in parent or not isinstance(parent[name], h5.Dataset):
            raise Exception(f'Path {name} is not a dataset in {parent.file.filename}:{parent.name}')

        super().__init__(au_parent, name)

        # Determine if this dataset supports direct appends.
        self.__supports_direct_appends = True
        meta = self.meta
        for col in meta['columns']:
            if meta['columns'][col]['type'] == 'string':
                self.__supports_direct_appends = False
                break

    @classmethod
    def new(cls, au_parent, name, value, overwrite=False, **kwargs):
        if not isinstance(au_parent, AUElement):
            raise Exception('Must send AUElement.')

        parent = au_parent._h5
        if not isinstance(parent, h5.Group):
            raise Exception(f'Invalid parent: {type(parent)}')

        if name in parent and not overwrite:
            raise Exception(f'{name} already exists.')

        # If given an HDF5 dataset or an AUDataset, read in all of its data
        # (HDF5 dataset as a numpy ndarray, AUDataset as a pandas DataFrame).
        if isinstance(value, (h5.Dataset, AUDataset)):
            value = value[:]

        # Try to create a class now.

        if isinstance(value, (np.ndarray, np.recarray)):
            return cls.__new_from_array(au_parent, name, value, **kwargs)

        elif isinstance(value, pd.DataFrame):
            return cls.__new_from_dataframe(au_parent, name, value)

        else:
            raise Exception(f'Unsure how to convert type {type(value)}')

    @classmethod
    def __new_from_array(cls, au_parent, name, arr,
        time_cols=set(), timedelta_cols=set()):

        meta, strings, recs = utils.audata_from_arr(arr, time_cols, timedelta_cols)
        au_parent._h5.create_dataset(
            name, chunks=True, maxshape=(None,),
            compression='gzip', shuffle=True, fletcher32=True, data=recs)
        au_parent._h5[name].attrs['.meta'] = utils.dict2json(meta)
        if len(strings) > 0:
            for strcol in strings:
                au_parent._h5.file.create_dataset(
                    f'.meta/strings/{name}/{strcol}', chunks=True, maxshape=(None,),
                    compression='gzip', shuffle=True, fletcher32=True,
                    dtype=h5.string_dtype(), data=strings[strcol])
        d = cls(au_parent, name)
        return d

    @classmethod
    def __new_from_dataframe(cls, au_parent, name, df):
        meta, strings, recs = utils.audata_from_df(df, time_ref=au_parent.file.time_reference)
        au_parent._h5.create_dataset(
            name, chunks=True, maxshape=(None,),
            compression='gzip', shuffle=True, fletcher32=True, data=recs)
        au_parent._h5[name].attrs['.meta'] = utils.dict2json(meta)
        if len(strings) > 0:
            for strcol in strings:
                au_parent._h5.file.create_dataset(
                    f'.meta/strings/{name}/{strcol}', chunks=True, maxshape=(None,),
                    compression='gzip', shuffle=True, fletcher32=True,
                    dtype=h5.string_dtype(), data=strings[strcol])
        d = cls(au_parent, name)
        return d

    def __getitem__(self, idx=slice(-1)):
        rec = self._h5[idx]
        if isinstance(rec, np.void):
            rec = np.array([rec], dtype=rec.dtype)
        meta = self.meta
        string_name = f'.meta/strings/{self.name}'
        string_ref = self._h5.file[string_name] if string_name in self._h5.file else None
        df = utils.df_from_audata(rec, meta, self.file.time_reference, string_ref, idx)
        return df

    def append(self, arr, direct=False):
        if direct and not self.supports_direct_appends:
            raise Exception('This dataset does not support direct appends.')
        elif not direct:
            # ATW: TODO:
            raise Exception('Not implemented yet.')

        N_data = len(arr)
        self._h5.resize((self.nrow + N_data,))
        self._h5[-N_data:] = arr

    @property
    def supports_direct_appends(self):
        return self.__supports_direct_appends

    @property
    def ncol(self):
        return len(self._h5.dtype)

    @property
    def nrow(self):
        return len(self._h5)

    @property
    def columns(self):
        return self.meta['columns']

    @property
    def shape(self):
        return (self.nrow(), self.ncol())

    def __repr__(self):
        def trunc(s, N=20):
            if len(s) > N:
                return s[:(N-3)] + '...'
            else:
                return s
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
