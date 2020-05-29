import h5py as h5
from audata.utils import json2dict, dict2json


class AUElement:
    def __init__(self, parent=None, name=''):
        if parent is None:
            self.parent = None
            self.file = None
            self._h5 = None
        elif isinstance(parent, h5.File):
            self.parent = self
            self.file = self
            self._h5 = parent
        elif isinstance(parent, AUElement):
            self.parent = parent
            self.file = parent.file
            self._h5 = parent._h5 if name == '' else parent._h5[name]
        else:
            raise Exception(f'Invalid parent: {type(parent)}.')

    def clear(self):
        self.parent = None
        self.file = None
        self._h5 = None

    @property
    def name(self):
        return self._h5.name if self._h5 is not None else None

    @property
    def filename(self):
        return self._h5.file.filename if self._h5 is not None else None

    @property
    def time_reference(self):
        return self.file.time_reference if self.file is not None else None

    @property
    def valid(self):
        return (self.parent is not None) and (self.file is not None) and (self._h5 is not None)

    @property
    def meta(self):
        return json2dict(self._h5.attrs['.meta']) \
            if self.valid and ('.meta' in self._h5.attrs) else None

    @meta.setter
    def meta(self, data):
        if not self.valid:
            raise Exception('Attempting to set meta on invalid element!')
        self._h5.attrs['.meta'] = dict2json(data)

    @property
    def meta_audata(self):
        return json2dict(self._h5.file['.meta'].attrs['audata']) if self.valid else None

    @property
    def meta_data(self):
        return json2dict(self._h5.file['.meta'].attrs['data']) if self.valid else None
