"""HDF5 file wrapper class."""
import os
import datetime as dt
from typing import Optional, Union, Literal

import tzlocal
import h5py as h5
from dateutil import parser

from audata import __VERSION__, __DATA_VERSION__
from audata._utils import dict2json
from audata.group import Group


class File(Group):
    """
    Wrapper around an HDF5 file.

    The wrapper adds a lot of convenience in handling audata files by automatically
    maintaining the correct underlying data schema while providing an intuitive
    interface and some convenience functions. Datasets can be accessed and updated
    by using a file object as a dictionary, a dictionary of dictionaries, or a dictionary
    where hierarchy is implied by use of the forward-slash as a "directory" delimiter,
    similar to how datasets are accessed using h5py. Data conversions to store higher-level
    data types unsupported natively by HDF5 (e.g., timestamps, ranges, or categorical
    variables) is handled implicitely.

    Generally, files are opened or created using the `open` or `new` class methods,
    respectively, instead of the constructor.

    Example:
        Creating a new file and adding a dataset:

        >>> f = audata.File.new('test.h5', time_reference=dt.datetime(2020, 5, 4, tzinfo=UTC))
        >>> f['data'] = pd.DataFrame(data={
        ...     'time': f.time_reference + dt.timedelta(hours=1)*np.arange(3),
        ...     'a': [1,2,3],
        ...     'b': pd.Categorical(['a', 'b', 'c'])})
        >>> f['data']
        /data: Dataset [3 rows x 3 cols]
          time: time
          a: integer (signed)
          b: factor with 3 levels [a, b, c]
        >>> f['data'][:]
                               time  a  b
        0 2020-05-04 00:00:00+00:00  1  a
        1 2020-05-04 01:00:00+00:00  2  b
        2 2020-05-04 02:00:00+00:00  3  c
    """
    DateTimeFormat = '%Y-%m-%d %H:%M:%S.%f %Z'

    def __init__(self,
                 file: h5.File,
                 time_reference: Optional[dt.datetime] = None,
                 return_datetimes: bool = True):
        """
        Instantiates the File object.

        Generally `new` or `open` will be called, the constructor is not called
        directly.

        Args:
            file: The opened HDF5 file object.
            time_reference: The file-level time reference.
            return_datetimes: True if timestamps should be converted to `dt.datetime` objects,
                False if Unix timestamps (UTC) should be returned instead.
        """
        if not isinstance(file, h5.File):
            raise ValueError(f'Invalid file type: {type(file)}')

        super().__init__(file)
        if time_reference is not None:
            self.time_reference = time_reference
        self.return_datetimes = return_datetimes

    def __del__(self):
        if self is not None:
            self.close()

    @property
    def time_reference(self) -> dt.datetime:
        """
        The timezone-aware time reference.

        Can be set with either a `dt.datetime` object or a `str` that can be parsed as
        a datetime. If a naive datetime is provided, the local timezone will be inferred.
        """
        return parser.parse(self.meta_data['time']['origin'])

    @time_reference.setter
    def time_reference(self, new_ref: Union[str, dt.datetime]):
        if not self.valid:
            raise Exception('Attempting to use uninitialized File!')

        # If it's a date/time string, that's fine, but try to parse it first to make sure
        # the format is always consistent.
        if isinstance(new_ref, str):
            new_ref = parser.parse(new_ref)

        # Now only accept datetime objects.
        if isinstance(new_ref, dt.datetime):
            # We need a timezone. If none is given, assume it's local time.
            if new_ref.tzinfo is None:
                new_ref = tzlocal.get_localzone().localize(new_ref)
            new_ref_str = new_ref.strftime(File.DateTimeFormat)

            data = self.meta_data
            data['time']['origin'] = new_ref_str
            self.hdf['.meta'].attrs['data'] = dict2json(data)

    @classmethod
    def new(cls,
            filename: str,
            overwrite: bool = False,
            time_reference: Union[Literal['now'], dt.datetime] = 'now',
            title: Optional[str] = None,
            author: Optional[str] = None,
            organization: Optional[str] = None,
            return_datetimes: bool = True,
            **kwargs) -> 'File':
        """
        Create a new file.

        Args:
            filename: The path of the file to open.
            overwrite: If True, existing files will be truncated. Otherwise, an
                existing file will cause an exception.
            time_reference: The time reference to use, or 'now' to use the time
                of file creation.
            title: A title for the dataset.
            author: The dataset author.
            organization: The dataset organization.
            return_datetimes: If True times will be converted to `dt.datetime` objects,
                otherwise Unix (UTC) timestamps.
            **kwargs: Additional keyword arguments will be passed on to `h5.File`'s constructor.

        Returns:
            The newly opened file object.
        """
        if os.path.exists(filename) and not overwrite:
            raise Exception('File "{}" already exists!'.format(filename))

        if time_reference == 'now':
            time_reference = dt.datetime.now(tz=tzlocal.get_localzone())

        h5_file = h5.File(filename, 'w', **kwargs)
        h5_file.create_group('.meta')
        h5_file['.meta'].attrs['audata'] = dict2json({
            'version': __VERSION__,
            'data_version': __DATA_VERSION__
        })
        h5_file['.meta'].attrs['data'] = dict2json({
            'title': title,
            'author': author,
            'organization': organization,
            'time': {
                'origin': time_reference.strftime(File.DateTimeFormat),
                'units': 'seconds'
            }
        })
        au_file = cls(h5_file,
                      time_reference=time_reference,
                      return_datetimes=return_datetimes)
        return au_file

    @classmethod
    def open(cls,
             filename: str,
             create: bool = False,
             readonly: bool = True,
             return_datetimes: bool = True,
             **kwargs) -> 'File':
        """
        Open an audata file.

        Args:
            filename: The path to the file to open.
            create: If True, missing files will be created. Otherwise, missing files
                cause an exception.
            readonly: Whether to open in read-only or mutable.
            return_datetimes: If True times will be converted to `dt.datetime` objects,
                otherwise Unix (UTC) timestamps.
            **kwargs: Additional keyword arguments will be passed on to `h5.File`'s constructor
                if a file is to be created.

        Returns:
            The opened file object.
        """
        if not os.path.exists(filename):
            if create:
                return cls.new(filename, **kwargs)
            else:
                raise Exception(f'File not found: {filename}')

        h5_file = h5.File(filename, 'r' if readonly else 'a')
        au_file = cls(h5_file, return_datetimes=return_datetimes)
        return au_file

    def close(self):
        """Close the file handle."""
        if self.hdf is not None:
            self.hdf.close()
            self.clear()

    def flush(self):
        """Flush changes to disk."""
        if self.hdf is not None:
            self.hdf.flush()
        else:
            raise Exception('No file opened!')

    def __repr__(self):
        return self.__getitem__('').__repr__()

    def __str__(self):
        return self.__getitem__('').__str__()

    def __enter__(self):
        return self

    def __exit__(self, exit_type, value, traceback):
        self.close()
