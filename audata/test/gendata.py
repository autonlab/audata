import pandas as pd
import numpy as np
import lorem
import os
import datetime as dt
import tzlocal


def ensure(fn):
    fn = 'patient123/{}'.format(fn)
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    return fn

time_reference = dt.datetime.now(tzlocal.get_localzone())
P = 60*30 # s

print('Making low-rate...')
Fs = 1./5 # Hz
N = int(Fs*P)
pd.DataFrame(
    data={
        'time': [time_reference + dt.timedelta(seconds=x/Fs) for x in range(N)],
        'time2': [time_reference + dt.timedelta(seconds=x/Fs + 0.5) for x in range(N)],
        'ints': list(range(N)),
        'floats': [i*1.1 for i in list(range(N))],
        'strings': [lorem.sentence() for x in range(N)],
        'factor': pd.Series([['Cat', 'Dog', 'Liger'][x % 3] for x in range(N)], dtype='category')
    }).to_csv(ensure('some_table.csv'), index=False)

print('Making 500Hz ECG...')
Fs = 500 # Hz
N = int(Fs*P)
pd.DataFrame(
    data={
        'time': [x/Fs for x in range(N)],
        'II': np.random.uniform(-2, 2, N),
        'III': np.random.uniform(-2, 2, N),
        'IV': np.random.uniform(-2, 2, N)
    }).to_csv(ensure('waveform/ecg.csv'), index=False)

print('Making 250Hz waveform...')
Fs = 250 # Hz
N = int(Fs*P)
pd.DataFrame(
    data={
        'time': [x/Fs for x in range(N)],
        'ART': np.random.uniform(50, 90, N),
        'PAP': np.random.uniform(10, 15, N),
        'CVP': np.random.uniform(0, 5, N)
    }).to_csv(ensure('waveform/pressures.csv'), index=False)

print('Making vitals...')
Fs = 1.5 # Hz
N = int(Fs*P)
pd.DataFrame(
    data={
        'time': [x/Fs for x in range(N)],
        'Sys': np.random.uniform(80, 90, N)
    }).to_csv(ensure('vitals/some_device/Sys.csv'), index=False)
pd.DataFrame(
    data={
        'time': [x/Fs for x in range(N)],
        'MAP': np.random.uniform(70, 80, N)
    }).to_csv(ensure('vitals/some_device/MAP.csv'), index=False)
pd.DataFrame(
    data={
        'time': [x/Fs for x in range(N)],
        'Dia': np.random.uniform(50, 65, N)
    }).to_csv(ensure('vitals/some_device/Dia.csv'), index=False)
