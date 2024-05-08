import math

from PyQt5.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utils.formatting import sub


class ControllerDialog(QDialog):
    def __init__(self, channels, udp_client, parent=None):
        super().__init__(parent)
        self.controller = ControllerWidget(channels, udp_client, parent=self)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OCMFET Controller")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.controller)
        self.setLayout(self.layout)


class ControllerWidget(QWidget):
    """
    Widget for controlling the OCMFET device
    """

    def __init__(self, channels, udp_client, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.channels = channels
        self.n_channels = len(channels)
        self.udp_client = udp_client
        self.init_ui()

    def init_ui(self):
        self.layout = QGridLayout()
        self.Ids_controls = {}
        self.Vg_controls = {}

        for i in range(self.n_channels):
            ch_type = self.channels[i]["type"]
            self.Ids_controls[i] = {}
            self.Vg_controls[i] = {}

            self.Ids_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Ids_controls[i]["spin_box"].setRange(0, 4)
            self.Ids_controls[i]["spin_box"].setSingleStep(0.1)
            self.Ids_controls[i]["spin_box"].setDecimals(2)
            self.Ids_controls[i]["spin_box"].setValue(0)

            if ch_type == 1:  # zero version
                self.Ids_controls[i]["spin_box"].setSuffix(" V")
            else:
                self.Ids_controls[i]["spin_box"].setSuffix(" \u03bcA")
                self.Ids_controls[i]["spin_box"].setPrefix("-")

            self.Ids_controls[i]["set_button"] = QToolButton(self)
            self.Ids_controls[i]["set_button"].setText("Set")
            self.Ids_controls[i]["reset_button"] = QToolButton(self)
            self.Ids_controls[i]["reset_button"].setText("Reset")

            self.Vg_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Vg_controls[i]["spin_box"].setRange(0, 4)
            self.Vg_controls[i]["spin_box"].setSingleStep(0.1)
            self.Vg_controls[i]["spin_box"].setDecimals(2)
            self.Vg_controls[i]["spin_box"].setValue(0)
            self.Vg_controls[i]["spin_box"].setPrefix("-")
            self.Vg_controls[i]["spin_box"].setSuffix(" V")
            self.Vg_controls[i]["set_button"] = QToolButton(self)
            self.Vg_controls[i]["set_button"].setText("Set")
            self.Vg_controls[i]["reset_button"] = QToolButton(self)
            self.Vg_controls[i]["reset_button"].setText("Reset")

            self.Ids_controls[i]["spin_box"].valueChanged.connect(
                lambda _, channel=i: self.Ids_controls[channel][
                    "spin_box"
                ].setStyleSheet("color: black")
            )
            self.Vg_controls[i]["spin_box"].valueChanged.connect(
                lambda _, channel=i: self.Vg_controls[channel][
                    "spin_box"
                ].setStyleSheet("color: black")
            )

            if ch_type == 1:
                self.Ids_controls[i]["set_button"].clicked.connect(
                    lambda _, channel=i: self.set_Vs(
                        channel, self.Ids_controls[channel]["spin_box"].value()
                    )
                )
                self.Ids_controls[i]["reset_button"].clicked.connect(
                    lambda _, channel=i: self.reset_Vs(channel)
                )
            else:
                self.Ids_controls[i]["set_button"].clicked.connect(
                    lambda _, channel=i: self.set_Ids(
                        channel, self.Ids_controls[channel]["spin_box"].value()
                    )
                )
                self.Ids_controls[i]["reset_button"].clicked.connect(
                    lambda _, channel=i: self.reset_Ids(channel)
                )

            self.Vg_controls[i]["set_button"].clicked.connect(
                lambda _, channel=i: self.set_Vg(
                    channel, self.Vg_controls[channel]["spin_box"].value()
                )
            )
            self.Vg_controls[i]["reset_button"].clicked.connect(
                lambda _, channel=i: self.reset_Vg(channel)
            )

        self.group_boxes = {}
        for i in range(self.n_channels):
            ch = self.channels[i]
            self.group_boxes[i] = QGroupBox(ch["name"])
            self.layout.addWidget(self.group_boxes[i], ch["coords"][0], ch["coords"][1])

            layout = QGridLayout()
            Ids_buttons = QHBoxLayout()
            Ids_buttons.addWidget(self.Ids_controls[i]["set_button"])
            Ids_buttons.addWidget(self.Ids_controls[i]["reset_button"])
            Vg_buttons = QHBoxLayout()
            Vg_buttons.addWidget(self.Vg_controls[i]["set_button"])
            Vg_buttons.addWidget(self.Vg_controls[i]["reset_button"])

            if ch_type == 1:
                layout.addWidget(QLabel("V" + sub("S")), 0, 0)
            else:
                layout.addWidget(QLabel("I" + sub("DS")), 0, 0)
            layout.addWidget(self.Ids_controls[i]["spin_box"], 1, 0)
            layout.addLayout(Ids_buttons, 2, 0)

            layout.addWidget(QLabel("V" + sub("G")), 0, 1)
            layout.addWidget(self.Vg_controls[i]["spin_box"], 1, 1)
            layout.addLayout(Vg_buttons, 2, 1)

            self.group_boxes[i].setLayout(layout)

        self.setLayout(self.layout)

    def send_command(self, command):
        self.udp_client.send_message(command)

    def set_Ids(self, channel, value):
        self.Ids_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"id{channel+1:02} {value:.2f}")

    def reset_Ids(self, channel):
        if not math.isclose(
            self.Ids_controls[channel]["spin_box"].value(), 0, abs_tol=1e-3
        ):
            self.Ids_controls[channel]["spin_box"].setStyleSheet("color: red")
        else:
            self.Ids_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"id{channel+1:02} 0")

    def set_Vg(self, channel, value):
        self.Vg_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"vg{channel+1:02} {value:.2f}")

    def reset_Vg(self, channel):
        if not math.isclose(
            self.Vg_controls[channel]["spin_box"].value(), 0, abs_tol=1e-3
        ):
            self.Vg_controls[channel]["spin_box"].setStyleSheet("color: red")
        else:
            self.Vg_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"vg{channel+1:02} 0")

    def set_Vs(self, channel, value):
        self.Ids_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"vs{channel+1:02} {value:.2f}")

    def reset_Vs(self, channel):
        if not math.isclose(
            self.Ids_controls[channel]["spin_box"].value(), 0, abs_tol=1e-3
        ):
            self.Ids_controls[channel]["spin_box"].setStyleSheet("color: red")
        else:
            self.Ids_controls[channel]["spin_box"].setStyleSheet("color: green")
        self.send_command(f"vs{channel+1:02} 0")
