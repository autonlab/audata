"""Script to generate some sample data."""
import os
import datetime as dt

import pandas as pd
import numpy as np
import lorem
import tzlocal

if __name__ == '__main__':

    def ensure(filename):
        """Ensure directory to store file exists."""
        filename = 'patient123/{}'.format(filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        return filename

    time_reference = dt.datetime.now(tzlocal.get_localzone())
    PERIOD = 60 * 30  # s

    print('Making low-rate...')
    SAMPLE_FREQ = 1. / 5  # Hz
    SAMPLES = int(SAMPLE_FREQ * PERIOD)
    pd.DataFrame(
        data={
            'time': [
                time_reference + dt.timedelta(seconds=x / SAMPLE_FREQ)
                for x in range(SAMPLES)
            ],
            'time2': [
                time_reference + dt.timedelta(seconds=x / SAMPLE_FREQ + 0.5)
                for x in range(SAMPLES)
            ],
            'ints':
                list(range(SAMPLES)),
            'floats': [i * 1.1 for i in list(range(SAMPLES))],
            'strings': [lorem.sentence() for x in range(SAMPLES)],
            'factor':
                pd.Series([['Cat', 'Dog', 'Liger'][x % 3]
                           for x in range(SAMPLES)],
                          dtype='category')
        }).to_csv(ensure('some_table.csv'), index=False)

    print('Making 500Hz ECG...')
    SAMPLE_FREQ = 500  # Hz
    SAMPLES = int(SAMPLE_FREQ * PERIOD)
    pd.DataFrame(
        data={
            'time': [x / SAMPLE_FREQ for x in range(SAMPLES)],
            'II': np.random.uniform(-2, 2, SAMPLES),
            'III': np.random.uniform(-2, 2, SAMPLES),
            'IV': np.random.uniform(-2, 2, SAMPLES)
        }).to_csv(ensure('waveform/ecg.csv'), index=False)

    print('Making 250Hz waveform...')
    SAMPLE_FREQ = 250  # Hz
    SAMPLES = int(SAMPLE_FREQ * PERIOD)
    pd.DataFrame(
        data={
            'time': [x / SAMPLE_FREQ for x in range(SAMPLES)],
            'ART': np.random.uniform(50, 90, SAMPLES),
            'PAP': np.random.uniform(10, 15, SAMPLES),
            'CVP': np.random.uniform(0, 5, SAMPLES)
        }).to_csv(ensure('waveform/pressures.csv'), index=False)

    print('Making vitals...')
    SAMPLE_FREQ = 1.5  # Hz
    SAMPLES = int(SAMPLE_FREQ * PERIOD)
    pd.DataFrame(
        data={
            'time': [x / SAMPLE_FREQ for x in range(SAMPLES)],
            'Sys': np.random.uniform(80, 90, SAMPLES)
        }).to_csv(ensure('vitals/some_device/Sys.csv'), index=False)
    pd.DataFrame(
        data={
            'time': [x / SAMPLE_FREQ for x in range(SAMPLES)],
            'MAP': np.random.uniform(70, 80, SAMPLES)
        }).to_csv(ensure('vitals/some_device/MAP.csv'), index=False)
    pd.DataFrame(
        data={
            'time': [x / SAMPLE_FREQ for x in range(SAMPLES)],
            'Dia': np.random.uniform(50, 65, SAMPLES)
        }).to_csv(ensure('vitals/some_device/Dia.csv'), index=False)
