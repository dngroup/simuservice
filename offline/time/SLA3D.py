# !/usr/bin/env python
# turn test.csv to proper time serie



import datetime
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import sklearn.cluster  # from mpl_toolkits.mplot3d import Axes3D

matplotlib.style.use('ggplot')


def remove_min_except_for_zeros(x):
    return x if len(x[x > 0]) == 0 else np.maximum(np.zeros(len(x)), x - min(x[x > 0]))


def generate_chunks(m):
    res = []
    while np.sum(m) > 0:
        m1 = np.apply_along_axis(remove_min_except_for_zeros, 0, m)
        res.append(m - m1)
        m = m1

    return res


def chunk_series_as_sla(series):
    index0 = list(series.items())[0][1].index
    keys = sorted(series.keys())
    m = np.array([series [key] for key in keys ])
    res = defaultdict(lambda: [])
    for sla in generate_chunks(m.T):
        for index, sla_slice in enumerate(sla.T[:], start=0):
            ssts = pd.Series(sla_slice, index=index0)
            ssts = ssts[ssts > 0]
            if len(ssts)>0:
                for range in np.split(ssts.index, np.where(np.diff(ssts.index) / pd.Timedelta('1H') != 1)[0] + 1):
                    res[keys[index]].append(pd.Series(np.max(ssts), index=range))

    return res


def chunk_series_as_sla2(series):
    aserie = series
    while len(list(aserie.keys())) > 0:
        res = defaultdict(
            lambda: (defaultdict(lambda: {})))  # { (begining_date,end_date):{serie1: bw, serie2: bw, sereien: bw},
        # (begining_date,end_date):{serie1: bw, serie2: bw, sereien: bw} }

        spans = defaultdict(lambda: [])
        min_obs_0 = np.max(list(aserie.items())[0][1].index)
        max_obs_0 = np.min(list(aserie.items())[0][1].index)

        for key, serie in list(aserie.items()):
            min_obs = min_obs_0
            max_obs = max_obs_0

            # get the spans
            for i in np.split(serie.index, np.where(np.diff(serie.index) / pd.Timedelta('1H') != 1)[0] + 1):
                if np.min(i) < min_obs:
                    min_obs = np.min(i)
                if np.max(i) > max_obs:
                    max_obs = np.max(i)
                spans[key] = i

        # list of date spans {(begining,end), (beginin, end) }
        sla_indexes = []
        # take the unions of the spans
        current_span = (None, None)
        for adate in pd.date_range(min_obs, max_obs, freq="H"):

            if any([adate in serie.index for serie in list(series.values())]):  # at least 1 serie has a value here
                if current_span[0] is None:
                    current_span = (adate, None)
            else:
                if current_span[1] is None:
                    sla_indexes.append((current_span[0], adate))
                    current_span = (None, None)

        # closure
        if current_span[1] is None:
            sla_indexes.append((current_span[0], adate))

        for span in sla_indexes:
            for key, serie in list(series.items()):
                res[span][key] = np.min(serie)

        minified_series = {}
        for key, serie in list(series.items()):
            serie = serie - np.min(serie)
            serie = serie[serie > 0]
            if len(serie) > 0:
                minified_series[key] = serie

        aserie = minified_series
    return res


def chunk_serie_as_sla(serie):
    res = []
    # as long as we have observations >0
    while not serie.empty:
        # take the min from the serie
        min = np.min(serie)
        # split whenever there's a gap in the observations
        for i in np.split(serie.index, np.where(np.diff(serie.index) / pd.Timedelta('1H') != 1)[0] + 1):
            # add the chunk
            res.append(pd.Series(min, index=i))
        # remove the min
        serie = serie - min
        # delete every null observation.
        serie = serie[serie > 0]
    return res


def get_tse(tsr, win, ncentroids=3):
    # tse=tsr.resample("%dH"%win).max().bfill()
    # tse=tse.rolling(window=win,center=True).max()
    # tse=tse.resample("1H").max().bfill()
    offset = pd.tseries.offsets.Hour(win)
    tsrr = tsr.resample("1H").bfill()
    tse = pd.Series(index=tsrr.index)
    start = tsr.index[0]
    end = tsr.index[-1]
    for i in range(0, int((end - start) / offset)):
        range_max = np.max(tsrr[(start + i * offset):(start + (i + 1) * offset)].values)
        tse[(start + i * offset):(start + (i + 1) * offset)] = range_max
    tse[(start + (i + 1) * offset):end] = np.max(tsrr[(start + (i + 1) * offset):end].values)
    fit = sklearn.cluster.KMeans(ncentroids).fit_predict(tse.values.reshape(-1, 1))
    for i in range(0, ncentroids):
        tse[fit == i] = max(tse.values * (fit == i))
    return tse


def get_3D_plot(ax3D, ratio=21, color="#ff0000"):
    # read data
    df = pd.read_csv("test2.csv", names=["time", "values"])
    # convert time column to proper time
    ts = pd.Series(data=df["values"].values,
                   index=df.apply(lambda row: datetime.datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                                  axis=1).values)
    # tsr=ts.resample("1H").max().ffill()
    tsr = ts
    MAX_WIN = 15
    MAX_CENTROID = 15
    X, Y = np.meshgrid(np.arange(2, MAX_WIN, 2), np.arange(2, MAX_CENTROID, 2))
    Z = np.array([price_slas(chunk_serie_as_sla(get_tse(tsr, x, y)), ratio=ratio) for (x, y) in
                  zip(X.ravel(), Y.ravel())]).reshape(Y.shape)
    Z = Z / np.min(Z) * 100

    surf = ax3D.plot_wireframe(X, Y, Z, color=color)

    return surf


if __name__ == "__main__":

    domain = np.arange(1, 100, 0.5)
    for key, i in enumerate(domain):
        fig = plt.figure()
        ax3D = fig.add_subplot(111, projection='3d')
        ax3D.set_zlim(95, 120)
        label = ax3D.set_xlabel('Window Size')
        label = ax3D.set_ylabel('Centroid Numbers')
        label = ax3D.set_zlabel('Price')
        ax3D.set_title("%03d" % i)
        # ax3D.set_axis_off()
        plot = get_3D_plot(ax3D, ratio=i, color="#ff0000")
        with open("plot%03d.png" % i, "w") as f:
            # print("%ld"%((1.0*key/len(domain))*360))
            plt.savefig(f, format='png')
            plt.close()
            # print("%03d"%i)


            # plt.show(block=False)
            # raw_input("...")
