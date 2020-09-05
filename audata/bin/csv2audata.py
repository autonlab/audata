"""Tool for automagically converting CSV files to audata files."""
import os
import argparse
from glob import glob
import datetime as dt
from typing import Optional

from dateutil.parser import parse, ParserError
import pandas as pd
import h5py as h5

import audata


def _mkfn(path: str) -> str:
    """Convert directory or CSV filename to h5 filename."""
    if os.path.isdir(path):
        return os.path.basename(path) + '.h5'
    else:
        return os.path.splitext(os.path.basename(path))[0] + '.h5'


def _addcsv(au_file: audata.File, name: str, path: str):
    """Add CSV file to the audata file."""
    data = pd.read_csv(path)
    for col in data.columns:
        # Does it have a name that can be interpreted as a "numeric" time?
        is_datetime = col.lower() in ('time', 'timestamp', 'index')
        is_str = data[col].dtype in (str, h5.string_dtype())

        if is_datetime or is_str:
            # Can we convert to date?
            if is_str:
                try:
                    _ = parse(data[col].values[0])
                    is_datetime = True
                except ParserError:
                    pass

            if is_datetime:
                if data[col].dtype in (str, h5.string_dtype()):
                    print('    Parsing time string column: {}'.format(col))
                    data[col] = data[col].apply(parse)
                else:
                    print('    Parsing time offset column: {}'.format(col))
                    data[col] = au_file.time_reference + data[col] * dt.timedelta(seconds=1)

            else:
                arity = len(data[col].unique())
                pct = float(arity) / len(data) * 100
                if pct > 10:
                    print('    Found string column: {} (arity {}%)'.format(
                        col, round(pct)))
                else:
                    print('    Parsing categorical column: {} (arity {} / {}%)'.
                          format(col, arity, round(pct)))
                    data[col] = pd.Series(data[col], dtype='category')
        else:
            print('    Found {} column: {}'.format(data[col].dtype, col))
    au_file[name] = data


def _walk(au_file: audata.File, path: str, prefix: Optional[str] = None):
    """Recurse a directory in search of CSV files to add."""
    if path is None or len(path) == 0 or path[0] == '.':
        return
    elif os.path.isdir(path):
        prefix = '' if prefix is None else os.path.basename(path)
        for next_path in glob('{}/*'.format(path)):
            _walk(au_file, next_path, prefix)
    elif os.path.splitext(path)[1].lower() == '.csv':
        if prefix is None:
            prefix = ''
        name = '{}{}{}'.format(prefix, '/' if prefix != '' else '',
                               os.path.splitext(os.path.basename(path))[0])
        print('  adding {}'.format(name))
        _addcsv(au_file, name, path)
    else:
        return


def main():
    """
    Converts CSV files or nested directories containing multiple CSVs to an audata HDF5 file.

    This tool takes in the path to either a single CSV file or a directory to be recursed for all
    CSV files. For each, it attempts to intelligently convert each CSV into an `audata` dataset
    and store the output to a file (with the same name as the CSV or directory, ending in '.h5').

    The tool will infer a datetime column if it is named time, timestamp, or index, or if it is a
    string column whose first element can be parsed as a datetime object using
    `dateutils.parser.parse`. This parsing does rely on the first row being valid.

    Other string columns will be treated either as factor/categorical columns if the arity (unique
    values) is less than 10% of the total number of rows, otherwise a string column.

    Args:
        path (str): Path to a CSV file or directory to be recursively scanned for CSVs.
    """
    parser = argparse.ArgumentParser(
        description=
        'Converts CSV files or nested directories containing multiple CSVs to an audata HDF5 file.'
    )
    parser.add_argument(
        'path',
        type=str,
        help=
        'Path to a CSV file or directory to be recursively scanned for CSVs.')
    args = parser.parse_args()

    filename = _mkfn(args.path)
    print('Creating {}'.format(filename))
    with audata.File.new(filename, overwrite=True) as au_file:
        _walk(au_file, args.path)
        print(au_file)


if __name__ == '__main__':
    main()
