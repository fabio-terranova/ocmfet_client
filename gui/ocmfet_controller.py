import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QPushButton,
                             QRadioButton, QSlider, QSpinBox, QVBoxLayout,
                             QWidget)

from utils.data_processing import sub


class ControllerWidget(QWidget):
    """
    Widget for controlling the OCMFET device

    """

    def __init__(self, n_channels, udp_client, zero=False, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.n_channels = n_channels
        self.n_rows = int(np.sqrt(n_channels))
        self.n_cols = int(np.ceil(n_channels/self.n_rows))
        self.udp_client = udp_client
        self.zero = zero
        self.init_ui()

    def init_ui(self):
        self.layout = QGridLayout()
        self.Ids_controls = {}
        self.Vg_controls = {}

        for i in range(self.n_channels):
            self.Ids_controls[i] = {}
            self.Vg_controls[i] = {}

            self.Ids_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Ids_controls[i]["spin_box"].setRange(0, 4)
            self.Ids_controls[i]["spin_box"].setSingleStep(0.1)
            self.Ids_controls[i]["spin_box"].setDecimals(2)
            self.Ids_controls[i]["spin_box"].setValue(0)
            self.Ids_controls[i]["spin_box"].setPrefix("-")

            if self.zero:
                self.Ids_controls[i]["spin_box"].setSuffix(" V")
            else:
                self.Ids_controls[i]["spin_box"].setSuffix(" \u03BCA")
            self.Ids_controls[i]["set_button"] = QPushButton("Set", self)
            self.Ids_controls[i]["reset_button"] = QPushButton("Reset", self)

            self.Vg_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Vg_controls[i]["spin_box"].setRange(0, 4)
            self.Vg_controls[i]["spin_box"].setSingleStep(0.1)
            self.Vg_controls[i]["spin_box"].setDecimals(2)
            self.Vg_controls[i]["spin_box"].setValue(0)
            self.Vg_controls[i]["spin_box"].setPrefix("-")
            self.Vg_controls[i]["spin_box"].setSuffix(" V")
            self.Vg_controls[i]["set_button"] = QPushButton("Set", self)
            self.Vg_controls[i]["reset_button"] = QPushButton("Reset", self)

            if self.zero:
                self.Ids_controls[i]["set_button"].clicked.connect(
                    lambda _, channel=i: self.set_Vs(
                        channel, self.Ids_controls[channel]["spin_box"].value()))
                self.Ids_controls[i]["reset_button"].clicked.connect(
                    lambda _, channel=i: self.reset_Vs(channel))
            else:
                self.Ids_controls[i]["set_button"].clicked.connect(
                    lambda _, channel=i: self.set_Ids(
                        channel, self.Ids_controls[channel]["spin_box"].value()))
                self.Ids_controls[i]["reset_button"].clicked.connect(
                    lambda _, channel=i: self.reset_Ids(channel))

            self.Vg_controls[i]["set_button"].clicked.connect(
                lambda _, channel=i: self.set_Vg(
                    channel, self.Vg_controls[channel]["spin_box"].value()))
            self.Vg_controls[i]["reset_button"].clicked.connect(
                lambda _, channel=i: self.reset_Vg(channel))

        self.group_boxes = {}
        for i in range(self.n_channels):
            self.group_boxes[i] = QGroupBox(f"Ch. {i+1}")
            self.layout.addWidget(
                self.group_boxes[i], i//self.n_cols, i % self.n_cols)

            layout = QGridLayout()

            if self.zero:
                layout.addWidget(QLabel("V" + sub("S")), 0, 0)
            else:
                layout.addWidget(QLabel("I" + sub("DS")), 0, 0)
            layout.addWidget(self.Ids_controls[i]["spin_box"], 1, 0)
            layout.addWidget(self.Ids_controls[i]["set_button"], 2, 0)
            layout.addWidget(self.Ids_controls[i]["reset_button"], 3, 0)

            layout.addWidget(QLabel("V" + sub("G")), 0, 1)
            layout.addWidget(self.Vg_controls[i]["spin_box"], 1, 1)
            layout.addWidget(self.Vg_controls[i]["set_button"], 2, 1)
            layout.addWidget(self.Vg_controls[i]["reset_button"], 3, 1)

            self.group_boxes[i].setLayout(layout)

        self.setLayout(self.layout)

    def send_command(self, command):
        self.udp_client.send_message(command)

    def set_Ids(self, channel, value):
        self.send_command(f"id{channel+1} {value}")

    def reset_Ids(self, channel):
        self.Ids_controls[channel]["spin_box"].setValue(0)
        self.send_command(f"id{channel+1} 0")

    def set_Vg(self, channel, value):
        self.send_command(f"vg{channel+1} {value}")

    def reset_Vg(self, channel):
        self.Vg_controls[channel]["spin_box"].setValue(0)
        self.send_command(f"vg{channel+1} 0")

    def set_Vs(self, channel, value):
        self.send_command(f"vs{channel+1} {value}")

    def reset_Vs(self, channel):
        self.Vg_controls[channel]["spin_box"].setValue(0)
        self.send_command(f"vs{channel+1} 0")
