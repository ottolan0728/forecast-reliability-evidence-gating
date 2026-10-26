"""Exact frozen causal feature function, extracted without scientific changes."""
import numpy as np
import pandas as pd

def features(y):
    x = pd.DataFrame({f'lag{k}': y.shift(k) for k in [1,2,3,24,48,168]})
    x['mean24'] = y.shift(1).rolling(24).mean()
    x['std24'] = y.shift(1).rolling(24).std()
    for name, values, period in [('hour',y.index.hour,24),('week',y.index.dayofweek,7),('year',y.index.dayofyear,366)]:
        x[name+'sin'] = np.sin(2*np.pi*values/period)
        x[name+'cos'] = np.cos(2*np.pi*values/period)
    return x
