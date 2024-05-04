import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QGridLayout,
                             QHBoxLayout, QLabel, QPushButton, QRadioButton,
                             QStyle, QToolButton, QVBoxLayout)

from gui.DataProcessing import DataProcessingWidget
from gui.MultiGraph import (MultiGraphPSDWidget, MultiGraphSpectrogramWidget,
                            MultiGraphWidget)
from utils.formatting import bytes2samples, s2string
from utils.processing import DataProcessor


class ChannelSelectionDialog(QDialog):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.channels = config["channels"]
        self.n_channels = len(self.channels)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Channels")

        self.layout = QVBoxLayout()
        self.grid = QGridLayout()
        self.ch_checkboxes = []
        for ch in self.channels:
            checkbox = QCheckBox(ch["name"])
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                self.update_channels)
            self.ch_checkboxes.append(checkbox)
            self.grid.addWidget(checkbox, ch["coords"][0], ch["coords"][1])

        self.layout.addLayout(self.grid)
        self.selall_button = QPushButton("Select all", self)
        self.selall_button.clicked.connect(self.select_all)
        self.dselall_button = QPushButton("Deselect all", self)
        self.dselall_button.clicked.connect(self.deselect_all)
        self.layout.addWidget(self.selall_button)
        self.layout.addWidget(self.dselall_button)
        self.setLayout(self.layout)

    def get_selected_channels(self):
        return [i for i, cb in enumerate(self.ch_checkboxes) if cb.isChecked()]

    def update_channels(self):
        self.parent().multi_graph.set_channels(self.get_selected_channels())
        self.parent().psd_widget.set_channels(self.get_selected_channels())
        self.parent().spectral_widget.set_channels(self.get_selected_channels())

    def select_all(self):
        for cb in self.ch_checkboxes:
            cb.setChecked(True)
        self.update_channels()

    def deselect_all(self):
        for cb in self.ch_checkboxes:
            cb.setChecked(False)
        self.update_channels()


class PlotDialog(QDialog):

    def __init__(self, config, data_listener, parent=None):
        super().__init__(parent)

        self.channels = config["channels"]
        self.n_channels = len(self.channels)
        self.fs = config["sample_rate"]
        self.tr = config["time_range"]
        self.time_ranges = config["time_ranges"]
        self.bandpass = config["bandpass"]
        self.notch = config["notch"]

        self.data_processer = DataProcessor(
            self.n_channels,
            self.fs,
            self.tr
        )

        self.processing_widget = DataProcessingWidget(
            self.fs,
            self.data_processer,
            self.bandpass,
            self.notch,
            self
        )

        self.channel_selection_dialog = ChannelSelectionDialog(config, self)

        self.data_listener = data_listener

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Live plotting")
        # add maximize button
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.multi_graph = MultiGraphWidget(
            self.channels,
            self.fs,
            self.tr,
            self
        )

        self.psd_widget = MultiGraphPSDWidget(
            self.channels,
            self.fs,
            self.tr,
            self
        )
        self.psd_widget.hide()

        self.spectral_widget = MultiGraphSpectrogramWidget(
            self.channels,
            self.fs,
            self.tr,
            self
        )
        self.spectral_widget.hide()

        self.glued_checkbox = QCheckBox("Glued")
        self.glued_checkbox.setChecked(True)
        self.timeseries_radio = QRadioButton("Time series")
        self.timeseries_radio.setChecked(True)
        self.timeseries_radio.clicked.connect(self.change_plot)
        self.compact_view_checkbox = QCheckBox("Compact")
        self.compact_view_checkbox.setChecked(False)
        self.compact_view_checkbox.stateChanged.connect(
            self.multi_graph.set_compact)
        self.psd_radio = QRadioButton("PSD")
        self.psd_radio.clicked.connect(self.change_plot)
        self.spectrogram_radio = QRadioButton("Spectrogram")
        self.spectrogram_radio.clicked.connect(self.change_plot)
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_plots)
        self.stream_button = QToolButton(self)
        self.stream_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPause))
        self.stream_button.setEnabled(self.data_listener.listening)
        self.stream_button.clicked.connect(self.pause_plots)
        self.time_range_label = QLabel("Time range")
        self.time_range_combo = QComboBox(self)
        self.time_range_combo.addItems(
            [s2string(tr) for tr in self.time_ranges])
        self.time_range_combo.setCurrentIndex(
            self.time_ranges.index(self.tr))
        self.time_range_combo.activated.connect(
            self.update_time_range)
        self.channel_sel_button = QPushButton("Channels", self)
        self.channel_sel_button.clicked.connect(
            self.channel_selection_dialog.exec_)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.multi_graph)
        self.layout.addWidget(self.psd_widget)
        self.layout.addWidget(self.spectral_widget)
        self.footer_layout = QHBoxLayout()
        self.footer_layout.addWidget(self.glued_checkbox)
        self.footer_layout.addStretch()
        self.freq_layout = QVBoxLayout()
        self.ts_layout = QHBoxLayout()
        self.ts_layout.addWidget(self.timeseries_radio)
        self.ts_layout.addWidget(self.compact_view_checkbox)
        self.freq_layout.addLayout(self.ts_layout)
        self.freq_layout.addWidget(self.psd_radio)
        self.freq_layout.addWidget(self.spectrogram_radio)
        self.footer_layout.addLayout(self.freq_layout)
        self.footer_layout.addWidget(self.processing_widget)
        self.live_layout = QGridLayout()
        self.live_layout.addWidget(self.stream_button, 0, 0)
        self.live_layout.addWidget(self.clear_button, 0, 1)
        self.live_layout.addWidget(self.time_range_label, 1, 0)
        self.live_layout.addWidget(self.time_range_combo, 1, 1)
        self.live_layout.addWidget(self.channel_sel_button, 2, 0, 1, 2)
        self.footer_layout.addLayout(self.live_layout)
        self.layout.addLayout(self.footer_layout)

        self.setLayout(self.layout)

    def update_data(self, data, ch_type):
        """
        Update the data of the plot dialog.

        Parameters
        ----------
        data : bytes
            Data to be plotted.
        """
        points = bytes2samples(np.array(data), ch_type)

        self.data_processer.update_data(points)
        if self.multi_graph.isVisible():
            self.multi_graph.update_curves(self.data_processer.get_data())
        elif self.psd_widget.isVisible():
            self.psd_widget.update_curves(self.data_processer.get_data())
        elif self.spectral_widget.isVisible():
            self.spectral_widget.update_curves(self.data_processer.get_data())

    def clear_plots(self):
        self.data_processer.clear_data()
        self.multi_graph.clear_plots()

    def pause_plots(self):
        """
        Pause or resume the plotting of the data.
        """
        if self.data_listener.listening:
            self.data_listener.stop_listening()
            self.stream_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.data_listener.start_listening()
            self.stream_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))

    def update_time_range(self, index):
        """
        Update the time range of the plot dialog.

        Parameters
        ----------
        index : int
            Index of the time range in the time_ranges list.
        """
        self.time_range = self.time_ranges[index]
        self.data_listener.set_bytes_to_emit(
            200*self.n_channels*int(self.fs*self.time_range)
        )
        self.data_processer.change_max_time(self.time_range)
        self.multi_graph.change_time_range(self.time_range)

        self.psd_widget.change_time_range(self.time_range)
        self.spectral_widget.change_time_range(self.time_range)

    def change_plot(self):
        """
        Change the plot mode, i.e., time series, PSD or spectrogram.
        """
        if self.timeseries_radio.isChecked():
            self.multi_graph.show()
            self.psd_widget.hide()
            self.spectral_widget.hide()
        elif self.psd_radio.isChecked():
            self.multi_graph.hide()
            self.psd_widget.show()
            self.spectral_widget.hide()
        elif self.spectrogram_radio.isChecked():
            self.multi_graph.hide()
            self.psd_widget.hide()
            self.spectral_widget.show()

        self.compact_view_checkbox.setEnabled(
            self.timeseries_radio.isChecked())

    def connect(self):
        """
        Connect the data listener to the plot dialog.
        """
        self.data_listener.received_data.connect(self.update_data)
        self.stream_button.setEnabled(True)

    def disconnect(self):
        """
        Disconnect the data listener from the plot dialog.
        """
        self.data_listener.received_data.disconnect(self.update_data)
        self.stream_button.setEnabled(False)

    def moveEvent(self, event):
        if self.glued_checkbox.isChecked():
            self.parent().move(self.x() - self.parent().width(), self.y())
        event.accept()

    def showEvent(self, event):
        self.connect()
        self.data_listener.start_listening()
        self.stream_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPause))

        # title_bar_height = self.parent().frameGeometry().height() - \
        #     self.parent().height()
        self.setGeometry(
            self.parent().x() + self.parent().width(),
            self.parent().y(),
            self.sizeHint().width(),
            int(self.sizeHint().width()*3/4)
        )
        event.accept()

    def closeEvent(self, event):
        self.data_listener.stop_listening()
        self.disconnect()
        event.accept()
