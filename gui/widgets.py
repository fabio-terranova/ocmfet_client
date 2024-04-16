from collections import deque

import numpy as np
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.Qt import mkQApp
from pyqtgraph.widgets.RemoteGraphicsView import RemoteGraphicsView

import pyqtgraph as pg


class RemoteGraphicsLayoutWidget(RemoteGraphicsView):
    """
    RemoteGraphicsLayoutWidget class

    This class is a wrapper around the RemoteGraphicsView class. It is used
    to create a remote graphics layout widget.
    """

    def __init__(self, parent=None, show=False, size=None, title=None, **kargs):
        mkQApp()
        RemoteGraphicsView.__init__(self, parent)
        self.ci = GraphicsLayout(**kargs)
        for n in ['nextRow', 'nextCol', 'nextColumn', 'addPlot', 'addViewBox', 'addItem', 'getItem', 'addLayout', 'addLabel', 'removeItem', 'itemIndex', 'clear']:
            setattr(self, n, getattr(self.ci, n))
        self.setCentralItem(self.ci)

        if size is not None:
            self.resize(*size)

        if title is not None:
            self.setWindowTitle(title)

        if show is True:
            self.show()


class MultiRemoteGraph(pg.GraphicsLayoutWidget):
    """
    Multigraph class

    This class uses the RemoteGraphicsLayoutWidget class to create a multi-graph.
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
        It should be a tuple with two strings: the axis label and the units, 
        e.g. ("Time", "s")

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
        self.x_label = ("bottom",) + x_label
        self.y_label = ("left",) + y_label
        self.initUI()

        self.init_data(self.fs, self.ms)

    def initUI(self):
        """ Initialize the UI of the widget."""
        for i in range(self.n):
            self.plot_items.append(self.addPlot(row=i, col=0))
            self.plot_items[i].setDownsampling(True, mode="peak")
            self.plot_items[i].setMenuEnabled(False)

            self.plot_items[i].setLabel(*self.x_label)
            ch_y_label = (
                self.y_label[0], f"({i+1}) " + self.y_label[1], self.y_label[2])
            self.plot_items[i].setLabel(*ch_y_label)

            # Link x-axis of all plots
            if i > 0:
                self.plot_items[i].setXLink(self.plot_items[0])

        self.curves = [self.plot_items[i].plot() for i in range(self.n)]

        # Set same red color for all curves
        for curve in self.curves:
            curve.setPen((255, 0, 0))

    def init_data(self, fs, tr):
        self.max_samples = int(fs*tr*1e3)

        if hasattr(self, "data_queues"):
            for i in range(self.n):
                self.data_queues[i] = deque(
                    list(self.data_queues[i]), maxlen=self.max_samples)
            self.ptr = len(self.data_queues[0])
        else:
            self.data_queues = [deque(maxlen=self.max_samples)
                                for _ in range(self.n)]
            self.ptr = 0

        for i in range(self.n):
            self.plot_items[i].setXRange(0, self.max_samples)

    def update_scroll(self, n, data):
        if self.ptr > self.max_samples:
            self.data_queues[n].popleft()
        self.data_queues[n].extend(data)
        self.curves[n].setData(self.data_queues[n])
        # Write RMS value
        rms = np.sqrt(np.mean(np.square(data)))
        self.plot_items[n].setTitle(f"RMS: {rms:.2e} A")

        self.ptr += len(data)

    def clear_scrolls(self):
        self.ptr = 0
        for i in range(self.n):
            self.data_queues[i].clear()
            self.curves[i].setData(self.data_queues[i])
