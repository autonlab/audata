import pandas as pd
import numpy as np

import datetime as dt
from dateutil import parser
import lorem

from .. import AUFile


f = AUFile.new('test.h5', overwrite=True)

# Writing a matrix.
f['mymat'] = np.ones([100, 300])

# Writing a data frame.
N = 1000
f['mydf'] = pd.DataFrame(
    data={
        'time': [f.time_reference + dt.timedelta(seconds=x/250.0) for x in range(N)],
        'time2': [f.time_reference + dt.timedelta(seconds=x/250.0 + 0.5) for x in range(N)],
        'ints': list(range(N)),
        'floats': [i*1.1 for i in list(range(N))],
        'strings': [lorem.sentence() for x in range(N)],
        'factor': pd.Series([['Cat', 'Dog', 'Liger'][x % 3] for x in range(N)], dtype='category')
    }
)

# Annotations - Not yet.
# f['mydf'].add_range('time', 'time2')

# Read some data.
print(f)
print(f['.meta'])
print(f.time_reference)
print(f._f['.meta/strings/mydf/strings'])
print(f['mydf'])
print(f['mydf'][:])

f.close()

# Open the created file and do the same thing.
print('Testing openeing file we just created:')
f = AUFile.open('test.h5')

# Read some data.
print(f)
print(f['.meta'])
print(f.time_reference)
print(f._f['.meta/strings/mydf/strings'])
print(f['mydf'])
print(f['mydf'][:])

f.close()
