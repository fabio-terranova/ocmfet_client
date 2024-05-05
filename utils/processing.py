"""
DataProcessor module

This module contains the DataProcessor class for processing the data from the acquisition
system.
"""

from collections import deque

import numpy as np
from scipy.signal import filtfilt


class DataProcessor:
    """
    DataProcessor

    This class is used to process the data from the acquisition system. It stores
    the data in a deque object, and it can filter the data using the filters
    defined in the filters attribute.

    Parameters
    ----------
    n : scalar
        Number of channels

    fs : scalar
        Sample rate in kHz

    max_time : scalar
        Maximum time in s

    filters : list
        List of tuples with the filter coefficients. Each tuple should have
        two arrays, the numerator and the denominator of the filter transfer
        function.

    Attributes
    ----------
    n : scalar
        Number of channels

    fs : scalar
        Sample rate in kHz

    max_time : scalar
        Maximum time in s

    max_samples : scalar
        Maximum number of samples per channel

    filters : list
        List of tuples with the filter coefficients. Each tuple should have
        two arrays, the numerator and the denominator of the filter transfer
        function.

    data : list
        List of deques with the data of each channel

    ptr : scalar
        Pointer to the last sample stored in the data

    Methods
    -------
    init_data()
        Initialize the data structure of the DataProcessor object.

    change_fs(fs)
        Change the sample rate of the DataProcessor object.

    change_max_time(max_time)
        Change the maximum time of the DataProcessor object.

    change_filters(filters)
        Change the filters of the DataProcessor object.

    filter_data(data)
        Filter the data using the filters of the DataProcessor object.

    update_data(data)
        Store new samples of data.

    get_data()
        Get the data stored in the DataProcessor object.

    clear_data()
        Clear the data stored in the DataProcessor object.
    """

    def __init__(self, n, fs, max_time, filters=[]):
        self.n = n
        self.fs = fs * 1e3
        self.max_time = max_time
        self.max_samples = int(self.fs * self.max_time)
        self.filters = filters

        self.init_data()

    def init_data(self):
        """ "
        Initialize the data structure of the DataProcessor object.
        """
        self.max_samples = int(self.fs * self.max_time)
        if hasattr(self, "data"):
            self.data = [
                deque(self.data[i], maxlen=self.max_samples) for i in range(self.n)
            ]
            self.ptr = len(self.data[0])
        else:
            self.data = [deque(maxlen=self.max_samples) for _ in range(self.n)]
            self.ptr = 0

    def change_fs(self, fs):
        """
        Change the sample rate of the DataProcessor object.

        Parameters
        ----------
        fs : scalar
            Sample rate in kHz
        """
        self.fs = fs * 1e3
        self.init_data()

    def change_max_time(self, max_time):
        """
        Change the maximum time of the DataProcessor object.

        Parameters
        ----------
        max_time : scalar
            Maximum time in s
        """
        self.max_time = max_time
        self.init_data()

    def change_filters(self, filters):
        """
        Change the filters of the DataProcessor object.

        Parameters
        ----------
        filters : list
            List of tuples with the filter coefficients. Each tuple should have
            two arrays, the numerator and the denominator of the filter transfer
            function.
        """
        self.filters = filters

    def filter_data(self, data):
        """
        Filter the data using the filters of the DataProcessor object.

        Parameters
        ----------
        data : array-like
            Data to be filtered. The data is the time series of a single channel.

        Returns
        -------
        data : ndarray
            Filtered data.
        """
        for b, a in self.filters:
            data = filtfilt(b, a, data)

        return data

    def update_data(self, data):
        """
        Store new samples of data. If the data exceeds the maximum number of samples,
        the oldest samples are removed.

        Parameters
        ----------
        data : array-like
            New samples to be added to the data. The data should be in the form
            [ch1_sample1, ch2_sample1, ..., ch1_sample2, ch2_sample2, ...], i.e.,
            the samples of each channel should be interleaved.
        """
        for i in range(self.n):
            if self.ptr > self.max_samples:
                self.data[i].popleft()
            self.data[i].extend(data[i :: self.n])
        self.ptr += len(data) // self.n  # Update pointer

    def get_data(self):
        """
        Get the data stored in the DataProcessor object. If filters are defined,
        the data is filtered before being returned.

        Returns
        -------
        data : ndarray
            Data stored in the DataProcessor object. The data is in the form
            [ch1_samples, ch2_samples, ...], i.e., the samples of each channel
            are stored in a separate array.
        """
        if self.filters:
            return np.array([self.filter_data(d) for d in self.data])
        else:
            return np.array(self.data)

    def clear_data(self):
        """
        Clear the data stored in the DataProcessor object.
        """
        self.ptr = 0
        for i in range(self.n):
            self.data[i].clear()
