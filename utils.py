import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def calc_cum_ma(array):  # function to calculate cumulative moving averages for an array

    moving_averages = list()
    cum_sum = np.cumsum(array)

    i = 1
    while i <= len(array):
        window_average = round(cum_sum[i - 1] / i, 3)
        moving_averages.append(window_average)

        i += 1
    return moving_averages


def calc_ma(array, size):  # function to calculate cumulative moving averages for an array

    # Convert array of integers to pandas series
    numbers_series = pd.Series(array)

    # Get the window of series of observations of specified window size
    windows = numbers_series.rolling(size)

    # Create a series of moving
    # averages of each window
    moving_averages = windows.mean()

    # Convert pandas series back to list
    moving_averages_list = moving_averages.tolist()

    return moving_averages_list


def find_spikes(array, std_threshold=0.5):
    ma = calc_cum_ma(array)
    std = np.std(array) * std_threshold
    threshold = [i + std for i in ma]

    spike_starts = list()
    spike_ends = list()

    in_spike = False
    for i in range(len(array)):
        if array[i] >= threshold[i] > array[i - 1] and in_spike is False:
            spike_starts.append(i)
            in_spike = True
        if array[i] <= threshold[i] < array[i - 1] and in_spike is True:
            spike_ends.append(i)
            in_spike = False

    # if a spike starts and continues until the end of the frame, we'll just consider the final index - 1 as the end
    if len(spike_starts) > len(spike_ends):
        spike_ends.append(int(len(array) - 1))
    return spike_starts, spike_ends, threshold


def find_ma_spikes(roi_array, ma_array, std_threshold=0.5):
    cum_ma = calc_cum_ma(roi_array)
    std = np.std(roi_array) * std_threshold
    threshold = [i + std for i in cum_ma]

    spike_starts = list()
    spike_ends = list()

    in_spike = False
    for i in range(len(ma_array)):
        if ma_array[i] >= threshold[i] > ma_array[i - 1] and in_spike is False:
            spike_starts.append(i - 2)
            in_spike = True
        if ma_array[i] <= threshold[i] < ma_array[i - 1] and in_spike is True:
            spike_ends.append(i)
            in_spike = False

    # if a spike starts and continues until the end of the frame, we'll just consider the final index - 1 as the end
    if len(spike_starts) > len(spike_ends):
        spike_ends.append(int(len(ma_array) - 1))
    return spike_starts, spike_ends, threshold


def plot_ma_spikes(roi_id, ma_size=20, std_ratio=0.5, plot=True, return_=False):
    # this function will calculate and plot spikes found using the following definition:
    # spike begins when MA20 crosses 0.5 standard deviations above the cumulative moving average

    roi = list(df.iloc[roi_id])[1:]
    roi_ma = calc_ma(roi, size=ma_size)

    starts, ends, threshold = find_ma_spikes(roi, roi_ma, std_threshold=std_ratio)

    if plot:
        plt.figure(figsize=(10, 5))
        plt.plot(roi)
        plt.plot(roi_ma, color='k')
        plt.plot(threshold, color='y')

        for i in range(len(starts)):
            plt.axvline(x=starts[i], color='goldenrod', linestyle='dashdot')
            plt.axvline(x=ends[i], color='goldenrod', linestyle='dashdot')

    if return_:
        return starts, ends, roi


def calc_integral(spike, cum_ma):
    floor = cum_ma[i]
    norm_spike = [round(point - floor, 3) for point in spike]
    integral = np.trapz(norm_spike)
    return integral
