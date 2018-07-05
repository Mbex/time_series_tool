import pandas as pd
import datetime as dt
import numpy as np
import dateutil


def _get_index(array, value):

    """Return nearest date index to value passed."""

    idx = (np.abs(array - dateutil.parser.parse(value))).argmin()
    return idx


def _get_times(df, s, e):

    """
    Returns the closest dates in the index of a df
    to those provided. Must be dt.datime objects.
    If default values of 0 are provided, start and
    end times are those of the entire data set
    """

    if s != 0:
        s = _get_index(df.index, s)

    if e == 0:
        e = len(df)-1
    else:
        e = _get_index(df.index, e)

    return df.index[s], df.index[e]


def nan_points(df, df_col, s=0, e=0, threshold=1e20):

    """
    NaN all entries between (s)tart and (e)nd time.
    df requires datetime index. Default values of
    s and e take first and last entries of the df.
    Threshold changed where the value is made null.
    """

    s, e = _get_times(df, s, e)
    series = df[df_col].copy()
    series[(series < threshold) & (series.index > s) & (series.index < e)] = np.nan

    return series


def normalise(df, df_col, nto):

    """
    Normalise df_col to nto.
    Returns Series.
    """

    n_factor = np.nanmean(df[nto]) / df[nto]
    series = (df[df_col] * n_factor).copy()

    return series


def remove_background(df, df_col, bg_val, s=0, e=0):

    """
    Remove a uniform value from a times series.
    Return a series.
    """

    s, e = get_times(df, s, e)
    series = df.iloc[s:e, df_col].copy()
    series -= bg_val
    return series


def calibrate(df, df_col, cf, s=0, e=0):

    """
    Calibrate times series by dividing with
    calibration factor.
    Return a series.
    """

    s, e = get_times(df, s, e)
    series = df[s:e][df_col].copy()
    series /= cf
    return series


def delete_column(df, df_col):

    """Remove column from dataframe."""

    df.drop(df_col, inplace=True, axis=1)


def rename_column(df, df_col, new_n):

    """Rename column in dataframe."""

    df.rename(columns={df_col:new_n}, inplace=True)
