import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QGridLayout,
                             QHBoxLayout, QLabel, QPushButton, QRadioButton,
                             QVBoxLayout)

from gui.DataProcessingWidget import DataProcessingWidget
from gui.MultiGraphWidget import (MultiGraphPSDWidget,
                                  MultiGraphSpectrogramWidget,
                                  MultiGraphWidget)
from utils.data_processer import DataProcesser
from utils.formatting import bytes2samples, s2string, sub


class PlotDialog(QDialog):

    def __init__(self, config, data_listener, parent=None):
        super().__init__(parent)

        self.zero = config["zero"]
        self.ch_layout = config["ch_layout"]
        self.n_channels = len(self.ch_layout)
        self.fs = config["sample_rate"]
        self.tr = config["time_range"]
        self.time_ranges = config["time_ranges"]
        self.bandpass = config["bandpass"]
        self.notch = config["notch"]

        self.data_processer = DataProcesser(
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

        self.data_listener = data_listener

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Live plotting")
        # add maximize button
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        if self.zero:
            y_label = (f"I{sub('ds')}", "A")
        else:
            y_label = (f"&Delta;I{sub('ds')}", "A")

        self.multi_graph = MultiGraphWidget(
            self.ch_layout,
            self.fs,
            self.tr,
            ("Time", "s"),
            y_label,
            parent=self
        )

        self.psd_widget = MultiGraphPSDWidget(
            self.ch_layout,
            self.fs,
            self.tr,
        )
        self.psd_widget.hide()

        self.spectral_widget = MultiGraphSpectrogramWidget(
            self.ch_layout,
            self.fs,
            self.tr,
            ("Time", "s"),
            ("Frequency", "Hz"),
        )
        self.spectral_widget.hide()

        self.glued_checkbox = QCheckBox("Glued")
        self.glued_checkbox.setChecked(True)
        self.timeseries_radio = QRadioButton("Time series")
        self.timeseries_radio.setChecked(True)
        self.timeseries_radio.clicked.connect(self.change_plot)
        self.psd_radio = QRadioButton("PSD")
        self.psd_radio.clicked.connect(self.change_plot)
        self.spectrogram_radio = QRadioButton("Spectrogram")
        self.spectrogram_radio.clicked.connect(self.change_plot)
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_plots)
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setEnabled(self.data_listener.listening)
        self.pause_button.clicked.connect(self.pause_plots)
        self.time_range_label = QLabel("Time range")
        self.time_range_combo = QComboBox(self)
        self.time_range_combo.addItems(
            [s2string(tr) for tr in self.time_ranges])
        self.time_range_combo.setCurrentIndex(
            self.time_ranges.index(self.tr))
        self.time_range_combo.currentIndexChanged.connect(
            self.update_time_range)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.multi_graph)
        self.layout.addWidget(self.psd_widget)
        self.layout.addWidget(self.spectral_widget)
        self.footer_layout = QHBoxLayout()
        self.footer_layout.addWidget(self.glued_checkbox)
        self.footer_layout.addStretch()
        self.freq_layout = QVBoxLayout()
        self.freq_layout.addWidget(self.timeseries_radio)
        self.freq_layout.addWidget(self.psd_radio)
        self.freq_layout.addWidget(self.spectrogram_radio)
        self.footer_layout.addLayout(self.freq_layout)
        self.footer_layout.addWidget(self.processing_widget)
        self.live_layout = QGridLayout()
        self.live_layout.addWidget(self.clear_button, 0, 0)
        self.live_layout.addWidget(self.pause_button, 0, 1)
        self.live_layout.addWidget(self.time_range_label, 1, 0)
        self.live_layout.addWidget(self.time_range_combo, 1, 1)
        self.footer_layout.addLayout(self.live_layout)
        self.layout.addLayout(self.footer_layout)

        self.setLayout(self.layout)

    def update_time_range(self, idx):
        self.time_range = self.time_ranges[idx]
        self.data_listener.set_bytes_to_emit(
            128*int(self.fs*self.time_range)
        )

    def update_data(self, data):
        points = bytes2samples(np.array(data), self.zero)

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
        if self.data_listener.listening:
            self.data_listener.stop_listening()
            self.pause_button.setText("Pause")
        else:
            self.data_listener.start_listening()
            self.pause_button.setText("Resume")

    def update_time_range(self, index):
        self.time_range = self.time_ranges[index]
        self.data_listener.set_bytes_to_emit(
            128*int(self.fs*self.time_range)
        )
        self.data_processer.change_max_time(self.time_range)
        self.multi_graph.change_time_range(self.time_range)

        self.psd_widget.change_time_range(self.time_range)
        self.spectral_widget.change_time_range(self.time_range)

    def change_plot(self):
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

    def connect(self):
        self.data_listener.received_data.connect(self.update_data)
        self.pause_button.setEnabled(True)

    def disconnect(self):
        self.data_listener.received_data.disconnect(self.update_data)
        self.pause_button.setEnabled(False)

    def showEvent(self, event):
        self.connect()

        title_bar_height = self.parent().frameGeometry().height() - \
            self.parent().height()

        self.setGeometry(
            self.parent().x() + self.parent().width(),
            self.parent().y() + title_bar_height,
            600,
            self.parent().height()
        )
        event.accept()

    def closeEvent(self, event):
        self.disconnect()
        event.accept()
