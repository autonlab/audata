"""
Classes for wrapping HDF5 datasets.
"""
from typing import Union, AbstractSet, Optional, Tuple, Any, Dict

import numpy as np
import pandas as pd
import h5py as h5

from audata import _utils as utils
from audata.element import Element


class Dataset(Element):
    """
    Maps to an HDF5 dataset, maintaining the `audata` schema and facilitating translation of
    higher-level data types. Generally should not be instantiated directly.
    """

    def __init__(self, au_parent: Element, name: str):
        if not isinstance(au_parent, Element):
            raise Exception(f'Invalid parent: {type(au_parent)}')

        parent = au_parent.hdf
        if not isinstance(parent, h5.Group):
            raise Exception(f'Invalid parent: {type(parent)}')

        if name not in parent or not isinstance(parent[name], h5.Dataset):
            raise Exception(
                f'Path {name} is not a dataset in {parent.file.filename}:{parent.name}'
            )

        super().__init__(au_parent, name)

    @classmethod
    def new(cls,
            au_parent: Element,
            name: str,
            value: Union[h5.Dataset, np.ndarray, np.recarray, pd.DataFrame],
            overwrite: bool = False,
            **kwargs) -> 'Dataset':
        """Create a new Dataset object."""

        if not isinstance(au_parent, Element):
            raise Exception('Must send Element.')

        parent = au_parent.hdf
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
                         au_parent: Element,
                         name: str,
                         arr: Union[np.ndarray, np.recarray],
                         time_cols: Optional[AbstractSet[str]] = None,
                         timedelta_cols: Optional[AbstractSet[str]] = None
                        ) -> 'Dataset':
        """Create a new dataset from a numpy recarray or ndarray."""

        if time_cols is None:
            time_cols = set({})
        if timedelta_cols is None:
            timedelta_cols = set({})

        # ATW: TODO: Less lame.
        if arr.dtype.names is None:
            return cls.__new_from_dataframe(au_parent, name,
                                            pd.DataFrame(data=arr))

        meta, recs = utils.audata_from_arr(
            arr,
            time_ref=au_parent.file.time_reference,
            time_cols=time_cols,
            timedelta_cols=timedelta_cols)
        au_parent.hdf.create_dataset(name,
                                     chunks=True,
                                     maxshape=(None,),
                                     compression='gzip',
                                     shuffle=True,
                                     fletcher32=True,
                                     data=recs)
        au_parent.hdf[name].attrs['.meta'] = utils.dict2json(meta)
        dataset = cls(au_parent, name)
        return dataset

    @classmethod
    def __new_from_dataframe(cls,
                             au_parent: Element,
                             name: str,
                             data: pd.DataFrame,
                             time_cols: Optional[AbstractSet[str]] = None,
                             timedelta_cols: Optional[AbstractSet[str]] = None
                            ) -> 'Dataset':
        """Create a new dataset from a pandas DataFrame."""

        if time_cols is None:
            time_cols = set({})
        if timedelta_cols is None:
            timedelta_cols = set({})

        meta, recs = utils.audata_from_df(
            data,
            time_ref=au_parent.file.time_reference,
            time_cols=time_cols,
            timedelta_cols=timedelta_cols)
        au_parent.hdf.create_dataset(name,
                                     chunks=True,
                                     maxshape=(None,),
                                     compression='gzip',
                                     shuffle=True,
                                     fletcher32=True,
                                     data=recs)
        au_parent.hdf[name].attrs['.meta'] = utils.dict2json(meta)
        dataset = cls(au_parent, name)
        return dataset

    def __getitem__(self, idx=slice(-1)) -> pd.DataFrame:
        return self.get(idx)

    def get(self,
            idx=slice(-1),
            raw: Optional[bool] = False,
            datetimes: Optional[bool] = None) -> pd.DataFrame:
        """Return a dataset as a pandas DataFrame."""

        rec = self.hdf[idx]
        if raw:
            return rec
        if isinstance(rec, np.void):
            rec = np.array([rec], dtype=rec.dtype)

        if datetimes is None:
            datetimes = self.file.return_datetimes
        data = utils.df_from_audata(rec, self.columns, self.file.time_reference, datetimes)
        return data

    def append(self,
               data: Union[pd.DataFrame, np.recarray],
               direct: bool = False,
               time_cols: Optional[AbstractSet[str]] = None,
               timedelta_cols: Optional[AbstractSet[str]] = None):
        """Append additional data to a dataset."""

        if time_cols is None:
            time_cols = set({})
        if timedelta_cols is None:
            timedelta_cols = set({})

        arr = None
        if isinstance(data, np.recarray):
            arr = data
            if not direct:
                _, arr = utils.audata_from_arr(arr,
                                               time_ref=self.time_reference,
                                               time_cols=time_cols,
                                               timedelta_cols=timedelta_cols)
        elif direct:
            raise ValueError(
                ('Data must be in a recarray already to use direct append! '
                 f'Instead {type(data)} was sent.'))
        elif isinstance(data, pd.DataFrame):
            # Issue 3: This does not validate categorical levels. So keep them the same!
            _, arr = utils.audata_from_df(data,
                                          time_ref=self.time_reference,
                                          time_cols=time_cols,
                                          timedelta_cols=timedelta_cols)

        data_len = len(arr)
        self.hdf.resize((self.nrow + data_len,))
        self.hdf[-data_len:] = arr

    @property
    def ncol(self) -> int:
        """Number of columns in dataset."""
        return len(self.hdf.dtype)

    @property
    def nrow(self) -> int:
        """Number of rows in dataset."""
        return len(self.hdf)

    @property
    def columns(self) -> Dict[str, Any]:
        """Get dictionary of column specifications."""

        # Get the column definitions from the dataset meta
        metacols = self.meta['columns'] if self.meta is not None and 'columns' in self.meta else {}

        # Get the column names from the dataset
        try:
            dscols = {colname: utils.get_coltype_from_dtype_only(self.hdf.dtype[colname]) for colname in self.hdf.dtype.names}
        except:
            dscols = {}

        # TODO: Handle non-compound datasets

        # Return a merge of the two, with meta cols overridding the dset cols.
        return {**dscols, **metacols}

    @property
    def shape(self) -> Tuple[int, int]:
        """Get dataset shape tuple (rows, cols)."""
        return (self.nrow(), self.ncol())

    def __repr__(self):

        def trunc(string, max_len=20):
            if not isinstance(string, str):
                string = f'{string}'

            if len(string) > max_len:
                return string[:(max_len - 3)] + '...'
            else:
                return string

        lines = []
        ncol = self.ncol
        nrow = self.nrow
        lines.append(f'{self.name}: Dataset [{nrow} rows x {ncol} cols]')
        cols = self.columns
        for col in cols:
            col_meta = cols[col]
            if col_meta['type'] == 'integer':
                tstr = 'integer ({})'.format(
                    'signed' if col_meta['signed'] else 'unsigned')
            elif col_meta['type'] == 'factor':
                nlevels = len(col_meta['levels'])
                lvls = ', '.join([
                    trunc(lvl) for lvl in col_meta['levels'][:min(3, nlevels)]
                ])
                if nlevels > 3:
                    lvls += ', ...'
                tstr = f'factor with {nlevels} levels [{lvls}]'
            else:
                tstr = col_meta['type']
            lines.append(f'  {col}: {tstr}')
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()
