"""
MultiGraphWidget module

This module contains the MultiGraphWidget class for plotting the data coming from
the server in real-time.
"""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from scipy.signal import spectrogram, welch

from utils.formatting import datetime_range, sup


class MultiGraphWidget(pg.GraphicsLayoutWidget):
    """
    MultiGraph class

    This class uses the GraphicsLayoutWidget class to create a multi-graph widget.
    The plots are arranged in a column, and the x-axis of all plots are linked.

    Parameters
    -----------
    ch_layout: list
        List with the layout of the channels, e.g., [(1, 1), (2, 1)]

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

    def __init__(self, ch_layout, fs, tr, x_label, y_label, parent=None, title=""):
        super().__init__(parent, title=title)

        self.ch_layout = ch_layout
        self.n = len(ch_layout)
        self.fs = fs*1e3
        self.tr = tr
        self.max_samples = int(self.fs*self.tr)
        self.x_label = x_label
        self.y_label = y_label

        self.initUI()
        self.init_x_values()

    def set_labels(self):
        for i in range(self.n):
            y_label = (f"<b>({i+1})</b> {self.y_label[0]}", self.y_label[1])
            self.plot_items[i].setLabels(
                bottom=self.x_label,
                left=y_label
            )

    def initUI(self):
        """ Initialize the UI of the widget."""
        self.plot_items = []
        self.curves = []

        for i in range(self.n):
            row = self.ch_layout[i][0]
            col = self.ch_layout[i][1]
            self.plot_items.append(self.addPlot(row=row, col=col))
            self.plot_items[i].setDownsampling(True, mode="peak")
            self.plot_items[i].setMenuEnabled(False)
            self.plot_items[i].setClipToView(False)
            self.plot_items[i].showGrid(x=True, y=True)

            # Link x-axis of all plots
            if i > 0:
                self.plot_items[i].setXLink(self.plot_items[0])

        self.curves = [self.plot_items[i].plot() for i in range(self.n)]

        # Set same red color for all curves
        for curve in self.curves:
            curve.setPen((255, 0, 0))

        self.set_labels()

    def change_sample_rate(self, fs):
        self.fs = fs*1e3
        self.init_x_values()

    def change_time_range(self, tr):
        self.tr = tr
        self.init_x_values()

    def init_x_values(self):
        self.max_samples = int(self.fs*self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)
        for pi in self.plot_items:
            pi.setXRange(0, self.tr)

    def update_curves(self, data):
        for i in range(self.n):
            self.update_curve(i, data[i])

    def update_curve(self, i, data):
        data = np.array(data)

        self.curves[i].setData(
            x=self.x_values[:len(data)],
            y=data
        )

    def clear_plots(self):
        for i in range(self.n):
            self.curves[i].clear()


class MultiGraph_dt(MultiGraphWidget):
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

        super().update_curves(data)


class MultiGraphPSDWidget(MultiGraphWidget):
    """ Wrapper for MultiGraphs class to plot the PSD of the data."""

    def __init__(self, n, fs, tr, parent=None):
        x_label = ("Frequency", "Hz")
        y_label = ("Linear spectrum", f"A{sup(2)}")
        super().__init__(n, fs, tr, x_label, y_label, parent, title="PSD")

    def initUI(self):
        super().initUI()

        for pi in self.plot_items:
            pi.setLogMode(x=True, y=True)

    def init_data(self, fs, tr):
        super().init_data(fs, tr)

        self.f_values = np.fft.rfftfreq(self.max_samples, d=1/self.fs)

    def init_x_values(self):
        self.max_samples = int(self.fs*self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)

    def update_curve(self, i, data):
        f, y = welch(
            data,
            self.fs,
            'flattop',
            scaling="spectrum",
            nperseg=len(data)//4
        )

        self.curves[i].setData(
            x=f,
            y=y
        )


cmap = pg.colormap.get('viridis')


class MultiGraphSpectrogramWidget(MultiGraphWidget):
    """ Spectrogram widget."""

    def __init__(self, n, fs, tr, x_label, y_label, parent=None):
        x_label = ("Time", "s")
        y_label = ("Frequency", "Hz")
        super().__init__(n, fs, tr, x_label, y_label, parent, title="Spectrogram")

    def initUI(self):
        """ Initialize the UI of the widget."""
        self.plot_items = []
        self.images = []

        for i in range(self.n):
            view = self.addPlot(i, 0)
            img = pg.ImageItem()
            view.addItem(img)

            self.plot_items.append(view)
            self.images.append(img)

        self.set_labels()

    def change_sample_rate(self, fs):
        self.fs = fs*1e3
        self.init_x_values()

    def change_time_range(self, tr):
        self.tr = tr
        self.init_x_values()

    def init_x_values(self):
        self.max_samples = int(self.fs*self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)

        for view in self.plot_items:
            view.setXRange(0, self.tr)
            view.setYRange(0, self.fs/2)

    def update_curves(self, data):
        for i in range(self.n):
            self.update_curve(i, data[i])

    def update_curve(self, i, data):
        data = np.array(data)

        # get the spectrogram
        f, t, Sxx = spectrogram(
            data, self.fs,
            nfft=1024,
        )

        # update the image
        self.images[i].setImage(
            np.log10(Sxx).T,
            autoLevels=True,
            lut=cmap.getLookupTable(0.0, 1.0, 256),
            autoDownsample=True,

        )

        self.images[i].setRect(QtCore.QRectF(0, 0, t[-1], f[-1]))

    def clear_plots(self):
        for i in range(self.n):
            self.images[i].clear()
