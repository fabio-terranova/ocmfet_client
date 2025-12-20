"""
MultiGraph module

This module contains the MultiGraphWidget class for plotting the data coming from the server in
real-time.
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from scipy.signal import spectrogram, welch

from ocmfet_client.utils.formatting import datetime_range, sup


class MultiGraphWidget(pg.GraphicsLayoutWidget):
    """
    MultiGraphWidget

    This class uses the GraphicsLayoutWidget class to create a multi-graph widget. The plots are
    arranged in a grid layout defined by the channels variable.

    Parameters
    -----------
    channels: list
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

    title : str
        Title of the widget
    """

    def __init__(self, channels, fs, tr, parent=None, title=""):
        super().__init__(parent, title=title)

        self.channels = channels
        self.n = len(channels)
        self.fs = fs * 1e3
        self.tr = tr
        self.max_samples = int(self.fs * self.tr)
        self.compact = False
        self.enabled_channels = [i for i in range(self.n)]
        # self.enabled_channels = [8, 9, 10, 11, 12, 13, 14, 15]

        self.initUI()
        self.init_x_values()

    def initUI(self):
        """Initialize the UI of the widget."""
        self.plot_items = []
        self.curves = []

        for i in range(self.n):
            row = self.channels[i]["coords"][0]
            col = self.channels[i]["coords"][1]
            self.plot_items.append(self.addPlot(row=row, col=col))
            self.plot_items[i].setDownsampling(True, mode="peak")
            self.plot_items[i].setClipToView(True)
            self.plot_items[i].showGrid(x=True, y=True)
            # self.plot_items[i].setRange(yRange=[-10e-6, 10e-6])
            self.plot_items[i].setTitle(f"<b>({i + 1})</b>")

        self.curves = [self.plot_items[i].plot() for i in range(self.n)]

        # Set same red color for all curves
        for curve in self.curves:
            curve.setPen((255, 0, 0))

        for i, ch in enumerate(self.channels):
            self.plot_items[i].setLabels(**ch["labels"])

    def change_sample_rate(self, fs):
        """
        Change the sample rate of the widget.

        Parameters
        ----------
        fs : scalar
            Sample rate in kHz
        """
        self.fs = fs * 1e3
        self.init_x_values()

    def change_time_range(self, tr):
        """
        Change the time range of the widget.

        Parameters
        ----------
        tr : scalar
            Time range in s
        """
        self.tr = tr
        self.init_x_values()

    def init_x_values(self):
        """Initialize the x values of the plots."""
        self.max_samples = int(self.fs * self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)
        for pi in self.plot_items:
            pi.setXRange(0, self.tr)
            pi.setXLink(self.plot_items[0])

    def update_curves(self, data):
        """Update the curves of the plots."""
        for i in self.enabled_channels:
            self.update_curve(i, data[i])

    def update_curve(self, i, data):
        """Update the curve of the i-th plot."""
        data = np.array(data)

        self.curves[i].setData(x=self.x_values[: len(data)], y=data)

    def clear_plots(self):
        """Clear the plots."""
        for curve in self.curves:
            curve.clear()

    def set_compact(self, compact):
        """Set the compact mode of the widget."""
        self.compact = compact
        for pi in self.plot_items:
            pi.showAxis("left", show=not compact)
            pi.showLabel("bottom", show=not compact)

    def set_channels(self, channels):
        """Set the enabled channels of the widget."""
        self.enabled_channels = channels


class MultiGraph_dt(MultiGraphWidget):
    """Wrapper for MultiRemoteGraph class with datetime x-axis."""

    def __init__(self, n, fs, tr, x_label, y_label, parent=None):
        super().__init__(n, fs, tr, x_label, y_label, parent)

    def init_x_values(self):
        self.x_values = datetime_range(self.max_samples, self.tr)

        for plot_item in self.plot_items:
            axis = pg.DateAxisItem(orientation="bottom")
            plot_item.setAxisItems({"bottom": axis})

    def update_curves(self, data):
        self.x_values = datetime_range(self.max_samples, self.tr)

        super().update_curves(data)


class MultiGraphPSDWidget(MultiGraphWidget):
    """Wrapper for MultiGraphs class to plot the PSD of the data."""

    def __init__(self, n, fs, tr, parent=None):
        super().__init__(n, fs, tr, parent, title="PSD")

    def initUI(self):
        super().initUI()

        for pi, ch in zip(self.plot_items, self.channels, strict=False):
            pi.setLogMode(x=True, y=True)
            y_unit = ch["labels"]["left"][1]
            labels = {
                "bottom": ("Frequency", "Hz"),
                "left": ("Linear spectrum", f"{y_unit}{sup(2)}"),
            }
            pi.setLabels(**labels)

    def init_data(self, fs, tr):
        super().init_data(fs, tr)

        self.f_values = np.fft.rfftfreq(self.max_samples, d=1 / self.fs)

    def init_x_values(self):
        self.max_samples = int(self.fs * self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)
        for pi in self.plot_items:
            pi.setYLink(self.plot_items[0])

    def update_curve(self, i, data):
        f, y = welch(
            data, self.fs, "flattop", scaling="spectrum", nperseg=len(data) // 4
        )

        self.curves[i].setData(x=f, y=y)


class MultiGraphSpectrogramWidget(MultiGraphWidget):
    """Spectrogram widget."""

    def __init__(self, n, fs, tr, parent=None):
        super().__init__(n, fs, tr, parent, title="Spectrogram")
        self.cmap = pg.colormap.get("viridis")

    def initUI(self):
        """Initialize the UI of the widget."""
        self.plot_items = []
        self.images = []

        for ch in self.channels:
            row = ch["coords"][0]
            col = ch["coords"][1]
            view = self.addPlot(row=row, col=col)
            img = pg.ImageItem()
            view.addItem(img)
            view.setLabels(left=("Frequency", "Hz"), bottom=ch["labels"]["bottom"])

            self.plot_items.append(view)
            self.images.append(img)

    def change_sample_rate(self, fs):
        self.fs = fs * 1e3
        self.init_x_values()

    def change_time_range(self, tr):
        self.tr = tr
        self.init_x_values()

    def init_x_values(self):
        self.max_samples = int(self.fs * self.tr)
        self.x_values = np.linspace(0, self.tr, self.max_samples)

        for view in self.plot_items:
            view.setXRange(0, self.tr)
            view.setYRange(0, self.fs / 2)

    def update_curve(self, i, data):
        data = np.array(data)

        # get the spectrogram
        f, t, Sxx = spectrogram(
            data,
            self.fs,
            nfft=1024,
        )

        # update the image
        self.images[i].setImage(
            np.log10(Sxx).T,
            autoLevels=True,
            lut=self.cmap.getLookupTable(0.0, 1.0, 256),
            autoDownsample=True,
        )

        # set the rect
        self.images[i].setRect(QtCore.QRectF(0, 0, t[-1], f[-1]))

    def clear_plots(self):
        for i in range(self.n):
            self.images[i].clear()
