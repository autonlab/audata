Format Specification
====================

Herein is presented the audata file format specification. The file format can easily be read & written without the `audata` package, though the package certainly makes things easier.

HDF5 Configuration
------------------

The audata file format is built upon the HDF5 format. HDF5 was chosen for many reasons, including to support streaming and compression. The audata package writes chunked datasets for streaming support and gzip compression for portability.

Data Hierarchy
--------------

At a high level, the audata standard doesn't enforce a particular data organization hierarchy, with the exception that groups prefixed with a period are considered meta-data or ignored. All other datasets are assumed to be valid data from which time series may be extracted. Metadata is stored as JSON text for ease of processing.

Metadata
--------

Global Metadata
***************

Global metadata is stored as a `.meta` JSON string atttribute on the built-in root group of the HDF5 file. The global metadata consists of high-level file information & configuration. It is also where string data are stored (similar to strings and cell-arrays in MATLAB's MAT files). Here is an example: ::

    .meta
        {
            # Software version.
            "version": [20, 2, 15, 1901],

            # Specification version.
            "data_version": 1

            "title": "...",
            "author": "...",
            "organization": "...",
            "time_origin": "2020-41-17 15:41:22.306880 EST",
        }

Anything can be stored in the global metadata `.meta`, but the most important entry that ideally should be present is the `time_origin`. All timestamps in the audata format are stored as offsets (seconds) from the origin specified in the meta. If no `time_origin` is included, then audata will assume that the offsets are epoch time.

Dataset Metadata
****************

Datasets may contain some meta data that document the data stored and indicate how to interpret it. The dataset metadata is optional but recommended. Comments are optional. Here is an example: ::

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


String Storage
--------------

String columns are stored as variable-length strings on HDF5's heap. Unfortunately this means they do not get compressed, but this is an issue that will be `resolved in the future`_.

.. _resolved in the future: https://github.com/autonlab/audata/issues/1

Note that factor (or categorical) columns are generally not treated the same way. Read about special data types below.

Groups
------

Groups may store meta data to override the time offset. Otherwise there are no restrictions on groups or hierarchy. For specific applications, a common schema may be desired (e.g. unifying medical datasets and naming conventions), but audata doesn't impose any restrictions or specifications on the presence or structure of groups. Use them to organize the data in a way that makes sense for your file or project.

Datasets
--------

Outside of the `.meta` group, any dataset is considered actual data. A dataset generally consists of at least two columns: a time and a value. However, neither is technically required. The usual assumption is that the first time column (usually the first column, usually named time) is present and is valid for all other columns, treated as signals with the same time index. However, audata is flexible and supports any number of time columns. It also supports the concept of a meta column derived from others, e.g., a time range derived from two time columns denoting the start and end of the range.

Special types
-------------

Dates and times are stored as double-precision values with units and origin specified in global `.meta` as indicated before. When stored or retrieved using the python library, this conversion happens seamlessly. This storage mechanism is inefficient for high-density, uniformly sampled data, which is `planned to be supported`_ in the future.

.. _planned to be supported: https://github.com/autonlab/audata/issues/2

Time deltas are also supported, also stored as double-precision in the indicated units. The designation is somewhat primarily for documentation but also allows automatic conversion to a timedelta object in python.

Strings were discussed previously.

Factor (or categorical) variables, even if the labels are strings, are treated differently. An integral index column is used to index into an array of factor levels, which are stored in the meta, not in the strings meta group. Automatic conversion happens when storing or reading via the python library.

The assumed difference between strings and factors is that factors are much lower arity than the size of the dataset (i.e., there are lots of repeats) versus free-text which is often unique to each entry. Typically, the number is quite small (say, less than 100) and the labels are short. This isn't always the case: a city might be a categorical, and there are many of those. But generally this assumption is reasonable, so when inferring data types while converting from other data sources the columns are usually treated as factor values if the arity is less than 10% of the data size, otherwise treated as strings.

Meta columns
------------

Certain meta columns are supported. The example above is the time range, which specifies two other columns as the start and end times. Meta columns can be interpreted as hints to higher-level structure in an otherwise flat table, or (as in the case of a time range) actually be interpreted as a usable data type (e.g., plotting time ranges with shading on a graph).

Currently just time ranges are supported as meta columns. Ranges specify columns with start and end times.
