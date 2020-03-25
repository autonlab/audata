import numpy as np
import pandas as pd
import h5py as h5

from . import utils


class AUDataset:
    def __init__(self, af, path):
        # if not isinstance(af, AUFile):
        #     raise Exception('Invalid AUFile file.')

        self._af = af

        if path not in self._af._f or not isinstance(self._af._f[path], h5.Dataset):
            raise Exception('Path {} is not a dataset in {}'.format(path, self._af._f.filename))

        self._path = path
        self._root = af._f[path]

    @classmethod
    def new(cls, af, path, value, overwrite=False):
        if path in af._f and not overwrite:
            raise Exception('{} already exists.'.format(path))

        if isinstance(value, pd.DataFrame):
            return cls.__new_from_dataframe(af, path, value)

    @classmethod
    def __new_from_dataframe(cls, af, path, df):
        meta, strings, recs = utils.audata_from_df(df, time_ref=af.time_reference)
        af._f.create_dataset(
            path, chunks=True, maxshape=(None,),
            compression='gzip', shuffle=True, fletcher32=True, data=recs)
        af._f[path].attrs['.meta'] = utils.dict2json(meta)
        if len(strings) > 0:
            for strcol in strings:
                af._f.create_dataset(
                    '.meta/strings/{}/{}'.format(path, strcol), chunks=True, maxshape=(None,),
                    compression='gzip', shuffle=True, fletcher32=True,
                    dtype=h5.string_dtype(), data=strings[strcol])
        return cls(af, path)

    def __getitem__(self, *args, **kwargs):
        rec = self._root.__getitem__(*args, **kwargs)
        meta = self.meta
        string_path = f'.meta/strings/{self._path}'
        string_ref = self._af._f['.meta/strings/{}'.format(self._path)] if string_path in self._af._f else None
        df = utils.df_from_audata(rec, meta, self._af.time_reference, string_ref)
        return df

    @property
    def meta(self):
        return utils.json2dict(self._root.attrs['.meta'])

    @property
    def ncol(self):
        return len(self._root.dtype)

    @property
    def nrow(self):
        return len(self._root)

    @property
    def shape(self):
        return (self.nrow(), self.ncol())

    def __repr__(self):
        def trunc(s, N=20):
            if len(s) > N:
                return s[:(N-3)] + '...'
            else:
                return s
        meta = self.meta
        lines = []
        ncol = self.ncol
        nrow = self.nrow
        lines.append('{}: Dataset [{} rows x {} cols]'.format(self._path, nrow, ncol))
        for col in meta['columns']:
            c = meta['columns'][col]
            if c['type'] == 'integer':
                tstr = 'integer ({})'.format('signed' if c['signed'] else 'unsigned')
            elif c['type'] == 'factor':
                nlevels = len(c['levels'])
                lvls = ', '.join([trunc(lvl) for lvl in c['levels'][:min(3,nlevels)]])
                if nlevels > 3:
                    lvls += ', ...'
                tstr = 'factor with {} levels [{}]'.format(nlevels, lvls)
            else:
                tstr = c['type']
            lines.append('  {}: {}'.format(col, tstr))
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()
