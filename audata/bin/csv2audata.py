import os
import argparse
from glob import glob
import pandas as pd
from dateutil.parser import parse, ParserError
import h5py as h5
import datetime as dt

import audata


def mkfn(path):
    if os.path.isdir(path):
        return os.path.basename(path) + '.h5'
    else:
        return os.path.splitext(os.path.basename(path))[0] + '.h5'

def addcsv(f, nm, path):
    df = pd.read_csv(path)
    for col in df.columns:
        # Does it have a name that can be interpreted as a "numeric" time?
        is_datetime = col.lower() in ('time', 'timestamp', 'index')
        is_str = df[col].dtype in (str, h5.string_dtype())

        if is_datetime or is_str:
            # Can we convert to date?
            if is_str:
                try:
                    _ = parse(df[col].values[0])
                    is_datetime = True
                except ParserError:
                    pass

            if is_datetime:
                if df[col].dtype in (str, h5.string_dtype()):
                    print('    Parsing time string column: {}'.format(col))
                    df[col] = df[col].apply(parse)
                else:
                    print('    Parsing time offset column: {}'.format(col))
                    df[col] = f.time_reference + df[col]*dt.timedelta(seconds=1)

            else:
                arity = len(df[col].unique())
                pct = float(arity)/len(df)*100
                if pct > 10:
                    print('    Found string column: {} (arity {}%)'.format(col, round(pct)))
                else:
                    print('    Parsing categorical column: {} (arity {} / {}%)'.format(
                        col, arity, round(pct)))
                    df[col] = pd.Series(df[col], dtype='category')
        else:
            print('    Found {} column: {}'.format(df[col].dtype, col))
    f[nm] = df

def walk(f, path, prefix=None):
    if path is None or len(path) == 0 or path[0] == '.':
        return
    elif os.path.isdir(path):
        prefix = '' if prefix is None else os.path.basename(path)
        for next_path in glob('{}/*'.format(path)):
            walk(f, next_path, prefix)
    elif os.path.splitext(path)[1].lower() == '.csv':
        if prefix is None:
            prefix = ''
        nm = '{}{}{}'.format(
            prefix, '/' if prefix != '' else '',
            os.path.splitext(os.path.basename(path))[0])
        print('  adding {}'.format(nm))
        addcsv(f, nm, path)
    else:
        return

def main():
    parser = argparse.ArgumentParser(
        description='Converts CSV files or nested directories containing multiple CSVs to an audata HDF5 file.')
    parser.add_argument('path', type=str, help='Path to a CSV file or directory to be recursively scanned for CSVs.')
    args = parser.parse_args()

    fn = mkfn(args.path)
    print('Creating {}'.format(fn))
    with audata.File.new(fn, overwrite=True) as f:
        walk(f, args.path)
        print(f)

if __name__ == '__main__':
    main()
