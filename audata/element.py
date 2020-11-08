"""Base element class."""
from typing import Optional, Union, Dict, Any
import h5py as h5

from audata._utils import json2dict, dict2json


class Element:
    """
    Represents an abstract `audata` element (e.g., files, groups, etc..) It should not
    be necessary to interact with this class directly.
    """

    def __init__(self,
                 parent: Optional[Union[h5.File, 'Element']] = None,
                 name: str = ''):
        if parent is None:
            self.parent = None
            self.file = None
            self._h5 = None
        elif isinstance(parent, h5.File):
            self.parent = self
            self.file = self
            self._h5 = parent
        elif isinstance(parent, Element):
            self.parent = parent
            self.file = parent.file
            self._h5 = parent._h5 if name == '' else parent._h5[name]
        else:
            raise Exception(f'Invalid parent: {type(parent)}.')

    def clear(self):
        """Clear members to reset class."""
        self.parent = None
        self.file = None
        self._h5 = None

    @property
    def hdf(self) -> Optional[h5.HLObject]:
        """Get wrapped HDF object."""
        return self._h5

    @property
    def name(self) -> Optional[str]:
        """Element name (`Optional[str]`, read-only)"""
        return self._h5.name if self._h5 is not None else None

    @property
    def filename(self) -> Optional[str]:
        """Path to file (`Optional[str]`, read-only)"""
        return self._h5.file.filename if self._h5 is not None else None

    @property
    def time_reference(self) -> Optional['dt.datetime']:
        """File time reference (`Optional[dt.datetime]`, read-only)"""
        return self.file.time_reference if self.file is not None else None

    @property
    def valid(self) -> bool:
        """Is element valid? (`bool`, read-only)"""
        return \
            self.parent is not None and \
            self.file is not None and \
            self._h5 is not None

    @property
    def meta(self) -> Dict[str, Any]:
        """Element meta data (HDF5 .meta attribute) (JSON dictionary)"""
        return json2dict(self._h5.attrs['.meta']) if self.valid and '.meta' in self._h5.attrs else {}

    @meta.setter
    def meta(self, data: Dict[str, Any]):
        if not self.valid:
            raise Exception('Attempting to set meta on invalid element!')
        self._h5.attrs['.meta'] = dict2json(data)

    @property
    def file_meta(self) -> Dict[str, Any]:
        """File metadata (HDF5 .meta attribute of the built-in root group) (JSON dictionary, read-only)"""

        # Get the .meta attribute if it exists, otherwise return empty object now
        try:
            ms = self._h5.file.attrs['.meta']
        except:
            print("File metadata not found.")
            return {}

        # Parse and return the .meta json object
        try:
            return json2dict(ms)
        except Exception as e:
            print(f"There was an error decoding the file metadata!\n\nMetadata JSON:\n{self._h5.file.attrs['.meta'][0]}\n\nJSON decode exception:\n{e}\n")
            return {}

    @file_meta.setter
    def file_meta(self, data: Dict[str, Any]):
        if not self.valid:
            raise Exception('Attempting to set file meta on invalid elemenet!')
        self._h5.file.attrs['.meta'] = dict2json(data)
