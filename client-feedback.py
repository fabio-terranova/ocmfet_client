# Fabio Terranova - 2023
# Client for the OCMFET acquisition system developed by Elbatech (feedback version)

import socket
import sys
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox,
                             QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMainWindow, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget, QLineEdit)

# pg.setConfigOptions(useOpenGL=True)
# pg.setConfigOption('antialias', True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

version = "1.0"
window_title = f"OCMFET client {version} - Fabio Terranova"

BUF_LEN = 32

time_ranges = ["1 s", "10 s", "30 s", "1 min"]
sample_rates = ["10 kHz", "22.7 kHz", "30 kHz", "40 kHz", "50 kHz"]

default = {
    "server_ip": "192.168.137.240",
    "msg_port": 8888,
    "data_port": 8889,
    "T2": 44,
    "n_channels": 2,
    "sample_rate": "22.7 kHz",
    "time_range": "1 s"
}


def bytes2samples(data):
    most_sig = data[0::2]
    least_sig = data[1::2]

    d = (np.left_shift(most_sig, 8) + least_sig)
    r = np.uint16(d + 0x8000)  # r = (unsigned short)((int)(d + 0x8000));
    f = r * 10 / 65536.0 - 5
    I = f * 0.2 / 1e6  # uA to A

    return I


def htmlify(string):
    return f"<html>{string}</html>"


def mathify(string):
    return f"<math>{string}</math>"


def sub(string):
    return f"<sub>{string}</sub>"


def string2ms(string):
    # Return time range in ms from string
    if string[-2:] == "ms":
        return int(float(string[:-3]))
    elif string[-3:] == "min":
        return int(float(string[:-4])*60e3)
    elif string[-1:] == "s":
        return int(float(string[:-2])*1e3)
    else:
        return int(string)


def string2hertz(string):
    # Return sample rate in Hz from string
    if string[-3:] == "kHz":
        return float(string[:-4])*1e3
    elif string[-3:] == "Hz":
        return float(string[:-3])
    else:
        return float(string)


def string2T(fs):
    # Return T2 in us from string of sample rate in Hz
    return float(1/string2hertz(fs))*1e6


class PlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDownsampling(True, mode="peak")
        self.setMenuEnabled(False)
        # self.setClipToView(True)

        self.fs = string2hertz(default["sample_rate"])
        self.ms = string2ms(default["time_range"])
        self.init_data(self.fs, self.ms)

        self.curve = self.plot()
        self.curve.setPen((255, 0, 0))

    def init_data(self, fs, tr):
        self.max_samples = int(fs*tr/1e3)

        # If self.data is already defined, keep the last max_samples samples
        if hasattr(self, "data_queue"):
            self.data_queue = deque(
                list(self.data_queue), maxlen=self.max_samples)
            self.ptr = len(self.data_queue)
        else:
            self.data_queue = deque(maxlen=self.max_samples)
            self.ptr = 0
        self.setXRange(0, self.max_samples, padding=0)

    def update_scroll(self, data):
        # if self.ptr < self.max_samples:
        #     self.setXRange(0, self.ptr, padding=0)
        if self.ptr > self.max_samples:
            # Remove the first self.ptr samples
            self.data_queue.popleft()
        self.data_queue.extend(data)
        self.curve.setData(self.data_queue)

        self.ptr += len(data)


class UDPClientGUI(QMainWindow):
    def __init__(self,
                 server_ip=default["server_ip"],
                 msg_port=default["msg_port"],
                 data_port=default["data_port"]):
        super().__init__()
        self.T2 = default["T2"]
        self.fs = string2hertz(default["sample_rate"])
        self.n_channels = default["n_channels"]
        self.time_range = string2ms(default["time_range"])
        self.recording = False
        self.paused = False
        self.streaming = False

        self.server_address = (server_ip, msg_port)
        self.msg_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind sockets to ports
        self.msg_socket.bind(("", msg_port))
        self.data_socket.bind(("", data_port))

        # Create two threads to listen for messages and data
        self.msg_thread = MessageListener(self.msg_socket)
        self.data_thread = DataListener(self.data_socket)
        self.msg_thread.received_msg.connect(self.update_console)
        self.data_thread.received_data.connect(self.update_data)
        # self.data_thread.received_data.connect(self.print_data)
        self.msg_thread.start()
        self.data_thread.start()

        self.initUI()
        self.console.append(f"Listening for messages on port {msg_port}...")
        self.console.append(f"Listening for data on port {data_port}...")

    def initUI(self):
        self.setWindowTitle(window_title)

        self.Ids_controls = {}
        self.Vg_controls = {}

        for i in range(self.n_channels):
            self.Ids_controls[i] = {}
            self.Vg_controls[i] = {}

            self.Ids_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Ids_controls[i]["spin_box"].setRange(-4, 0)
            self.Ids_controls[i]["spin_box"].setSingleStep(0.1)
            self.Ids_controls[i]["spin_box"].setDecimals(2)
            self.Ids_controls[i]["spin_box"].setValue(0.1)
            self.Ids_controls[i]["spin_box"].setSuffix(" \u03BCA")
            self.Ids_controls[i]["set_button"] = QPushButton("Set", self)
            self.Ids_controls[i]["reset_button"] = QPushButton("Reset", self)

            self.Vg_controls[i]["spin_box"] = QDoubleSpinBox(self)
            self.Vg_controls[i]["spin_box"].setRange(-4, 0)
            self.Vg_controls[i]["spin_box"].setSingleStep(0.1)
            self.Vg_controls[i]["spin_box"].setDecimals(2)
            self.Vg_controls[i]["spin_box"].setValue(0.1)
            self.Vg_controls[i]["spin_box"].setSuffix(" V")
            self.Vg_controls[i]["set_button"] = QPushButton("Set", self)
            self.Vg_controls[i]["reset_button"] = QPushButton("Reset", self)

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

        self.stream_button = QPushButton("Stream", self)
        self.stream_button.clicked.connect(self.stream_cb)

        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.record_cb)

        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setPlaceholderText(
            "Enter a name for the file (default: data)")
        self.name_line_edit.setMaxLength(32)

        self.tag_line_edit = QLineEdit(self)
        self.tag_line_edit.setPlaceholderText("Enter a tag (default: tag)")
        self.tag_line_edit.setMaxLength(32)
        self.tag_button = QPushButton("Tag", self)
        self.tag_button.setEnabled(False)
        self.tag_button.clicked.connect(self.tag_cb)

        self.reset_button = QPushButton("Reset dsPIC", self)
        self.reset_button.clicked.connect(self.reset_cb)

        self.restart_server_button = QPushButton("Restart server", self)
        self.restart_server_button.clicked.connect(self.kill_server_cb)
        self.restart_server_button.setEnabled(False)

        self.console = QTextEdit(self)
        self.console.setReadOnly(True)

        self.plot_widgets = {}
        for i in range(self.n_channels):
            self.plot_widgets[i] = PlotWidget(self)
            self.plot_widgets[i].n_samples = int(
                1e3/(self.T2)*string2ms(default["time_range"]))
            self.plot_widgets[i].setMinimumSize(400, 200)
            self.plot_widgets[i].setLabel("bottom", "Time", "Samples")
            self.plot_widgets[i].setLabel(
                "left", f"({i+1}) " + mathify(f"&Delta;I{sub('ds')}"), "A")

        self.clear_plot_button = QPushButton("Clear plot", self)
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.pause_streaming_button = QPushButton("Pause", self)
        self.pause_streaming_button.setEnabled(False)
        self.pause_streaming_button.clicked.connect(self.pause_stream)
        self.sample_rate_label = QLabel("Sample rate", self)
        self.sample_rate_combo = QComboBox(self)
        self.sample_rate_combo.addItems(sample_rates)
        self.sample_rate_combo.setCurrentIndex(sample_rates.index(
            default["sample_rate"]
        ))
        self.sample_rate_combo.currentIndexChanged.connect(
            self.update_sample_rate)
        self.time_range_label = QLabel("Time range", self)
        self.time_range_combo = QComboBox(self)
        self.time_range_combo.addItems([r for r in time_ranges])
        self.time_range_combo.setCurrentIndex(time_ranges.index("1 s"))
        self.time_range_combo.currentIndexChanged.connect(
            self.update_time_range)

        self.layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.rec_groupbox = QGroupBox("Recording")
        self.button_layout = QHBoxLayout()

        self.button_layout.addWidget(self.record_button)
        self.button_layout.addWidget(self.stream_button)
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.restart_server_button)

        self.group_boxes = {}
        for i in range(self.n_channels):
            self.group_boxes[i] = QGroupBox(f"Channel {i+1} settings")

            layout = QGridLayout()

            layout.addWidget(QLabel("I" + sub("DS")), 0, 0)
            layout.addWidget(self.Ids_controls[i]["spin_box"], 1, 0)
            layout.addWidget(self.Ids_controls[i]["set_button"], 2, 0)
            layout.addWidget(self.Ids_controls[i]["reset_button"], 3, 0)

            layout.addWidget(QLabel("V" + sub("G")), 0, 1)
            layout.addWidget(self.Vg_controls[i]["spin_box"], 1, 1)
            layout.addWidget(self.Vg_controls[i]["set_button"], 2, 1)
            layout.addWidget(self.Vg_controls[i]["reset_button"], 3, 1)

            self.group_boxes[i].setLayout(layout)
            self.left_layout.addWidget(self.group_boxes[i])

        self.tag_layout = QHBoxLayout()
        self.tag_layout.addWidget(self.tag_line_edit)
        self.tag_layout.addWidget(self.tag_button)
        self.rec_layout = QVBoxLayout()
        self.rec_layout.addLayout(self.button_layout)
        self.rec_layout.addWidget(self.name_line_edit)
        self.rec_layout.addLayout(self.tag_layout)
        self.rec_groupbox.setLayout(self.rec_layout)
        self.left_layout.addWidget(self.rec_groupbox)
        self.left_layout.addWidget(self.console)

        self.right_layout = QVBoxLayout()
        for i in range(self.n_channels):
            self.right_layout.addWidget(self.plot_widgets[i])
        self.time_layout = QHBoxLayout()
        self.time_layout.addStretch()
        self.time_layout.addWidget(self.clear_plot_button)
        self.time_layout.addWidget(self.pause_streaming_button)
        self.time_layout.addWidget(self.sample_rate_label)
        self.time_layout.addWidget(self.sample_rate_combo)
        self.time_layout.addWidget(self.time_range_label)
        self.time_layout.addWidget(self.time_range_combo)
        self.right_layout.addLayout(self.time_layout)

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)
        self.layout.setStretch(1, 4)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def send_command(self, command):
        self.msg_socket.sendto(command.encode(), self.server_address)

    def set_Ids(self, channel, value):
        self.send_command(f"id{channel+1} {-value}")

    def reset_Ids(self, channel):
        self.Ids_controls[channel]["spin_box"].setValue(0)
        self.send_command(f"id{channel+1} 0")

    def set_Vg(self, channel, value):
        self.send_command(f"vg{channel+1} {-value}")

    def reset_Vg(self, channel):
        self.Vg_controls[channel]["spin_box"].setValue(0)
        self.send_command(f"vg{channel+1} 0")

    def send_user_command(self):
        command = self.line_edit.toPlainText()
        self.send_command(command)

    def record_cb(self):
        if not self.recording:
            name = "data"
            if self.name_line_edit.text() != "":
                name = self.name_line_edit.text()
            self.send_command("rec " + name)
            self.recording = True
            self.record_button.setText("Pause")
            self.tag_button.setEnabled(True)
            if not self.streaming:
                self.data_thread.listening = True
                self.streaming = True
                self.pause_streaming_button.setEnabled(True)
            self.stream_button.setText("Save")
        else:
            if not self.paused:
                self.send_command("pause")
                self.paused = True
                self.record_button.setText("Resume")
                self.tag_button.setEnabled(False)
            else:
                self.send_command("resume")
                self.paused = False
                self.record_button.setText("Pause")
                self.tag_button.setEnabled(True)

    def stream_cb(self):
        if not self.streaming:
            self.data_thread.listening = True
            self.send_command("start")
            self.streaming = True
            self.stream_button.setText("Stop")
            self.pause_streaming_button.setEnabled(True)
        else:
            self.data_thread.listening = False
            self.send_command("stop")
            self.streaming = False
            self.stream_button.setText("Stream")
            if self.recording or self.paused:
                self.recording = False
                self.paused = False
                self.record_button.setText("Record")
            self.tag_button.setEnabled(False)
            self.pause_streaming_button.setEnabled(False)

    def reset_cb(self):
        self.send_command("reset")

    def kill_server_cb(self):
        self.send_command("kill")

    def tag_cb(self):
        tag = self.tag_line_edit.text()
        if tag == "":
            tag = "tag"

        self.send_command(f"tag {tag}")

    def update_console(self, msg):
        log = f"-> {msg}"
        self.console.append(log)

    def print_data(self, data):
        self.console.append(str(data))

    def update_data(self, data):
        points = bytes2samples(data)

        for i in range(self.n_channels):
            self.plot_widgets[i].update_scroll(points[i::self.n_channels])

    def clear_plot(self):
        for i in range(self.n_channels):
            self.plot_widgets[i].data_queue.clear()
            self.plot_widgets[i].ptr = 0
            self.plot_widgets[i].curve.setData(self.plot_widgets[i].data_queue)

    def pause_stream(self):
        if self.data_thread.listening:
            self.data_thread.listening = False
            self.pause_streaming_button.setText("Resume")
        else:
            self.data_thread.listening = True
            self.pause_streaming_button.setText("Pause")

    def update_time_range(self, index):
        self.time_range = string2ms(time_ranges[index])
        self.data_thread.update_bytes_to_emit(self.fs, self.time_range)

        for i in range(self.n_channels):
            self.plot_widgets[i].init_data(self.fs, self.time_range)

    def update_sample_rate(self, index):
        self.T2 = string2T(sample_rates[index])
        self.fs = string2hertz(sample_rates[index])

        for i in range(self.n_channels):
            self.plot_widgets[i].init_data(self.fs, self.time_range)

        self.send_command(f"sT2 {self.T2}")

    def closeEvent(self, event):
        # self.send_command("stop")
        self.msg_thread.terminate()
        self.data_thread.terminate()
        self.msg_socket.close()
        self.data_socket.close()
        event.accept()


class MessageListener(QThread):
    received_msg = pyqtSignal(str)

    def __init__(self, msg_socket):
        super().__init__()
        self.socket = msg_socket

    def run(self):
        while True:
            self.msg, _ = self.socket.recvfrom(512)
            self.received_msg.emit(self.msg.decode())


class DataListener(QThread):
    received_data = pyqtSignal(np.ndarray)

    def __init__(self, data_socket):
        super().__init__()
        self.listening = True
        self.socket = data_socket
        fs = string2hertz(default["sample_rate"])
        tr = string2ms(default["time_range"])
        self.update_bytes_to_emit(fs, tr)

    def update_bytes_to_emit(self, fs, tr):
        self.bytes_to_emit = int(128*fs*tr*1e-7)*4
        self.data_buffer = deque(maxlen=self.bytes_to_emit)

    def run(self):
        while True:
            data, _ = self.socket.recvfrom(BUF_LEN)
            if self.listening:
                self.data_buffer.extend(data)

                if len(self.data_buffer) >= self.bytes_to_emit:
                    self.received_data.emit(np.array(self.data_buffer))
                    self.data_buffer.clear()


if __name__ == '__main__':
    # Run Qt GUI
    app = QApplication(sys.argv)

    # Usage: client.py [server_ip]:[msg_port]
    if len(sys.argv) > 1:
        server_ip, msg_port = sys.argv[1].split(":")
        msg_port = int(msg_port)
        client = UDPClientGUI(server_ip, msg_port, msg_port+1)
    else:
        client = UDPClientGUI()

    client.show()
    sys.exit(app.exec_())
