# AUData

Auton Universal Data (audata) Library

## Overview

The audata library is intended to standardize time series data storage and access around a specification that is easy to understand, well-supported on all major operating systems and most popular programming languages, and supports advanced features like data-streaming and compression out of the box. To this end we've developed an interface to sit on top of the HDF5 file format to promote ease of data conversion and retrieval in a consistent and well-defined format.

## HDF5 Configuration

HDF5 was chosen to support compression and streaming. For streaming support chunked datasets are used, and gzip compression is used for portability.

## Data Heirarchy

At a high level, audata doesn't enforce any particular data heirarchy, with the exception that groups prefixed with a period are considered meta-data. All other datasets are assumed to be valid data from which time series may be extracted. Meta-data in the file is largely stored as JSON text for ease of processing.

### Global Meta

At the data root there is `.meta` directory with some high-level configuration, and where string data are stored (similar to strings and cell-arrays in MATLAB's MAT files). There are two attributes here: `audata` and `data`. `audata` stores some information about the software used to generate the file and the spec version, e.g.,

```
.meta/audata
    {
        # Software version.
        "version": [20, 2, 15, 1901],

        # Specification version.
        "data_version": 1
    }
```

`data` stores some information about the particular file, most importantly the time reference:

```
.meta/data
    {
        "title": "...",
        "author": "...",
        "organization": "...",
        "time": {
            "origin": "2020-41-17 15:41:22.306880 EST",
            "units": "seconds"
        }
    }
```

Anything can be stored in data, but the most important entry that _must_ be present is the time. All timestamps in the audata format are stored as offsets from the origin specified in the meta, so recovery of a specific time or date is only possible if the origin is present. The units are also important as they indicate the units for timestamps and time deltas. These can be overridden at the dataset level, but if missing the global offset and units are assumed.

### String Storage

To avoid either variable-length rows or requiring fixed-length strings in datasets, the text in text-columns are stored separately in auxiliary datasets in the `.meta/strings` folder. The rest of the path matches the name of the dataset and specific column, e.g., if a string column `nurse_notes` is present in `patients/larry/checkups` then the strings get stored in a dataset named `.meta/strings/patients/larry/checkups/nurse_notes`. In HDF5, there is no column present in the `checkups` dataset stored, but there is meta data indicating that the string is present, allowing retrieval of the data when reading into e.g. a pandas DataFrame.

Though it adds complexity, separate storage of strings allows avoiding variable-length rows (which makes fast indexing more difficult) or fixed-length strings (which wastes space, and doesn't support adding larger strings later on without some effort). So, for text-heavy datasets, the added complexity is the tradeoff chosen. However, with the python library abstracting that operation out, it's transparent to the user.

Note that factor (or categorical) columns are generally not treated the same way. Read about special data types below.

## Groups

Groups may store meta data to override the time offset. Otherwise there are no restrictions on groups or heirarchy. For specific applications a common schema may be desired (e.g., unifiying medical datasets and naming conventions) but audata doesn't impose any specific restrictions.

## Datasets

Outside of the `.meta` group, any dataset is considered actual data. A dataset generally consists of at least two columns: a time and a value. However, neither is technically required. The usual assumption is that the first time column (usually the first column, usually named time) is present and is valid for all other columns, treated as signals with the same time index. However, audata is flexible and supports any number of time columns. It also supports the concept of a meta column derived from others, e.g., a time range derived from two time columns denoting the start and end of the range.

### Meta

Datasets contain some meta data that document the data stored and indicate how to interpret it. Comments are optional.

```
alert_dataset/.meta
    {
        "columns": {
            "start_time": {
                "type": "time"
            },
            "end_time": {
                "type": "string"
            },
            "problem": {
                "type": "factor",
                "levels": ["Misconfigured", "Cracked", "On Fire"],
                "ordered": true
            },
            "device_temperature": {
                "type": "real"
            },
            "times_broken": {
                "type": "integer",
                "signed": false
            },
            "other_notes": {
                "type": "string"
                "comment": "This field just contains device maintenance notes."
            }
        },
        "meta-columns": {
            "alert_period": {
                "type": "time-range",
                "start": "start_time",
                "end": "end_time"
            }
        }
    }
```

### Special types

Dates and times are stored as double-precision values with units and origin specified in `.meta/data` as indicated before. When stored or retrieved using the python library, this conversion happens seamlessly.

Time deltas are also supported, also stored as double-precision in the indicated units. The designation is somewhat primarily for documentation but also allows automatic conversion to a timedelta object in python.

Strings were discussed previously. Free-text data is not stored in the dataset to avoid fixed-width strings or variable-length rows, instead a note of the string columns are indicated in a dataset's meta, so the strings must be retireved manually if needed. This is transparent in the python library.

Factor (or categorical) variables, even if the labels are strings, are treated differently. An integral index column is used to index into an array of factor levels, which are stored in the meta, not in the strings meta group. Automatic conversion happens when storing or reading via the python library.

The assumed difference between strings and factors is that factors are much lower arity than the size of the dataset (i.e., there are lots of repeats) versus free-text which is often unique to each entry. Typically, the number is quite small (say, less than 100) and the labels are short. This isn't always the case: a city might be a categorical, and there are many of those. But generally this assumption is reasonable, so when inferring datatypes while converting from other data sources the columns are usually treated as factor values if the arity is less than 10% of the data size, otherwise treated as strings.

### Meta columns

Certain meta columns are supported. The example above is the time range, which specifies two other columns as the start and end times. Meta columns can be interpreted as hints to higher-level structure in an otherwise flat table, or (as in the case of a time range) actually be interpretted as a useable data type (e.g., plotting time ranges with shading on a graph).

Currently just time ranges are supported as meta columns. Ranges specify columns with start and end times.

### Annotations

Annotations currently are stored external to the original data file. However, we're considering how to store them together, as often it will be desired to provide data with the annotations.

One idea may be to use an inline dot-prefixed group with the same name as the dataset, whose contents can all be considered as annotations. Dataset format for annotations would otherwise be identical.

## Data Conversion: csv2audata

The `csv2audata` tool converts individual CSV files or, if given a directory, a heirarchy of CSV files to the audata format, maintaining the original heirarchy. It will attempt to infer the intended CSV column data types but will of course not infer things like meta-columns or comments. Text columns are treated as factor columns if the arity (number of unique values) is less than 10% of the dataset size. Otherwise it will be treated as a free-text string column.

## Bulding

```
python setup.py bdist_wheel
pip install -U dist/*.whl
cd test
python write.py
```