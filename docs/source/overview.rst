Overview
========

The audata library is intended to standardize time series data storage and access
around a specification that is easy to understand, well-supported on all major operating
systems and most popular programming languages, and supports advanced features like
data-streaming and compression out of the box. To this end we've developed an interface
to sit on top of the HDF5 file format to promote ease of data conversion and retrieval in
a consistent and well-defined format.

The `audata` specification is a generic data format schema built on top of
HDF5 with the purpose of extending the supported data types above what is
built in to HDF5, and to overlay various helper functions relevant to time
series data. Though time series are not the only support data types, they're
the primary focus for this library. `audata` is built to support efficient
and pain-free streaming of data in real-time as well as indexing of very large
datasets for visualization and analytic tasks.

The package is `pip`-installable: ::

    pip install audata
