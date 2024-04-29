from collections import deque

import numpy as np
from scipy.signal import filtfilt


class DataProcesser():
    def __init__(self, n, fs, max_time, filters=[]):
        self.n = n
        self.fs = fs*1e3
        self.max_time = max_time
        self.max_samples = int(self.fs*self.max_time)
        self.filters = filters

        self.init_data()

    def init_data(self):
        self.max_samples = int(self.fs*self.max_time)
        if hasattr(self, 'data'):
            for i in range(self.n):
                self.data[i] = deque(self.data[i], maxlen=self.max_samples)
            self.ptr = len(self.data[0])
        else:
            self.data = [deque(maxlen=self.max_samples) for _ in range(self.n)]
            self.ptr = 0

    def change_fs(self, fs):
        self.fs = fs*1e3
        self.init_data()

    def change_max_time(self, max_time):
        self.max_time = max_time
        self.init_data()

    def change_filters(self, filters):
        self.filters = filters

    def filter_data(self, data):
        for (b, a) in self.filters:
            data = filtfilt(b, a, data)

        return data

    def update_data(self, data):
        for i in range(self.n):
            if self.ptr > self.max_samples:
                self.data[i].popleft()
            self.data[i].extend(data[i::self.n])
        self.ptr += len(data)//self.n  # Update pointer

    def get_data(self):
        if self.filters:
            return [self.filter_data(np.array(d)) for d in self.data]
        else:
            return self.data

    def clear_data(self):
        self.ptr = 0
        for i in range(self.n):
            self.data[i].clear()
