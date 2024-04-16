from collections import deque

import numpy as np
import pyqtgraph as pg
from matplotlib.ticker import EngFormatter

from utils.data_processing import datetime_range

eng_formatter = EngFormatter(unit='A')


class MultiGraph(pg.GraphicsLayoutWidget):
    """
    MultiGraph class

    This class uses the GraphicsLayoutWidget class to create a multi-graph widget.
    The plots are arranged in a vertical layout.

    Parameters
    -----------
    n : int
        Number of plots

    fs : scalar
        Sample rate in kHz

    tr : scalar
        Time range in s

    x_label : tuple
        It could be a tuple with two strings: the axis label, and the units, 
        e.g. ("Time", "s"), or a single string with the axis label.

    y_label : tuple
        It should be a tuple with two strings: the axis label, and the units,
        e.g. ("Current", "A")

    parent : QWidget
        Parent widget

    """

    def __init__(self, n, fs, tr, x_label, y_label, parent=None):
        super().__init__(parent)
        self.plot_items = []
        self.curves = []

        self.n = n
        self.fs = fs
        self.ms = tr
        self.x_label = x_label
        self.y_label = y_label
        self.initUI()

        self.init_data(self.fs, self.ms)

    def initUI(self):
        """ Initialize the UI of the widget."""
        for i in range(self.n):
            self.plot_items.append(self.addPlot(row=i, col=0))
            self.plot_items[i].setDownsampling(True, mode="peak")
            self.plot_items[i].setMenuEnabled(False)
            self.plot_items[i].showGrid(x=True, y=True)

            self.plot_items[i].setLabels(
                bottom=self.x_label,
                left=self.y_label
            )

            # Link x-axis of all plots
            if i > 0:
                self.plot_items[i].setXLink(self.plot_items[0])

        self.curves = [self.plot_items[i].plot() for i in range(self.n)]

        # Set same red color for all curves
        for curve in self.curves:
            curve.setPen((255, 0, 0))

    def init_x_values(self):
        self.x_values = np.linspace(0, self.tr, self.max_samples)

    def init_data(self, fs, tr):
        self.fs = fs
        self.tr = tr
        self.max_samples = int(fs*tr*1e3)
        self.init_x_values()

        if hasattr(self, "data_queues"):
            for i in range(self.n):
                self.data_queues[i] = deque(
                    list(self.data_queues[i]), maxlen=self.max_samples)
            self.ptr = len(self.data_queues[0])
        else:
            self.data_queues = [deque(maxlen=self.max_samples)
                                for _ in range(self.n)]
            self.ptr = 0

        self.plot_items[-1].setLabels(bottom=self.x_label)

    def update_scrolls(self, data):
        """
        Updates the data in the scrolls.

        Parameters
        ----------
        data : ndarray
            Data to be plotted in the scrolls. The data should be a 1D array with
            the data for each channel interleaved. For example, if there are 2 channels
            and 10 samples, the data should be [ch1_sample1, ch2_sample1, ch1_sample2, ...]
        """
        for i in range(self.n):
            self.update_scroll(i, data[i::self.n])

    def update_scroll(self, i, data):
        if self.ptr > self.max_samples:
            self.data_queues[i].popleft()
        self.data_queues[i].extend(data)

        self.curves[i].setData(
            x=self.x_values[:len(self.data_queues[i])],
            y=self.data_queues[i]
        )

        # Write RMS value
        rms = np.sqrt(np.mean(np.square(data)))
        self.plot_items[i].setTitle(
            f"({i+1}) RMS: {eng_formatter.format_data(rms)}")

        # Update pointer
        self.ptr += len(data)

    def clear_scrolls(self):
        self.ptr = 0
        for i in range(self.n):
            self.data_queues[i].clear()


class MultiGraph_dt(MultiGraph):
    """ Wrapper for MultiRemoteGraph class with datetime x-axis."""

    def __init__(self, n, fs, tr, x_label, y_label, parent=None):
        super().__init__(n, fs, tr, x_label, y_label, parent)

    def init_x_values(self):
        self.x_values = datetime_range(self.max_samples, self.tr)

        for plot_item in self.plot_items:
            axis = pg.DateAxisItem(orientation='bottom')
            plot_item.setAxisItems({'bottom': axis})

    def update_scrolls(self, data):
        self.x_values = datetime_range(self.max_samples, self.tr)

        super().update_scrolls(data)
