import pandas as pd
import h5py as h5


class Annotation:
    def __init__(self, root):
        if not isinstance(root, h5.HLObject):
            raise Exception('Invalid  HDF5 high-level object.')

        self._root = root

    @property
    def lines(self):
        if 'line' in self._root.attrs:
            return pd.DataFrame(data=self._root.attrs['line'])
        else:
            return pd.DataFrame()

    @property
    def vranges(self):
        if 'vrange' in self._root.attrs:
            return pd.DataFrame(data=self._root.attrs['vrange'])
        else:
            return None

    @property
    def tranges(self):
        if 'trange' in self._root.attrs:
            return pd.DataFrame(data=self._root.attrs['trange'])
        else:
            return None

    def add_time_range(self, t0, t1):
        df = self.tranges
