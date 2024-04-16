import socket

import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QPushButton, QSpinBox, QTextEdit,
                             QVBoxLayout, QWidget)

from gui.widgets import MultiGraph
from network.listeners import DataListener, MessageListener
from utils.data_processing import (bytes2samples, khertz2string, s2hhmmss,
                                   s2string, sub)

# pg.setConfigOptions(useOpenGL=True)
pg.setConfigOption('antialias', True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

version = "2.0"
window_title = f"OCMFET client {version} - Fabio Terranova"


class UDPClientGUI(QMainWindow):
    """
    Main window of the client.
    """

    def __init__(self, config):
        super().__init__()

        self.zero = config["zero"]
        self.server_ip = config["server_ip"]
        self.msg_port = config["msg_port"]
        self.data_port = config["data_port"]
        self.T2 = config["T2"]
        self.time_ranges = config["time_ranges"]
        self.sample_rates = config["sample_rates"]
        self.fs = config["sample_rate"]
        self.time_range = config["time_range"]
        self.n_channels = config["n_channels"]
        self.timer = config["timer"]
        self.max_record_time = config["max_record_time"]

        self.recording = False
        self.paused = False
        self.streaming = False

        self.server_address = (self.server_ip, self.msg_port)
        self.msg_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind sockets to ports
        self.msg_socket.bind(("", self.msg_port))
        self.data_socket.bind(("", self.data_port))

        # Create two threads to listen for messages and data
        self.msg_thread = MessageListener(self.msg_socket)
        self.data_thread = DataListener(
            self.data_socket,
            config["sample_rate"],
            config["time_range"],
            config["BUF_LEN"]
        )
        self.msg_thread.received_msg.connect(self.update_console)
        self.data_thread.received_data.connect(self.update_data)
        # self.data_thread.received_data.connect(self.print_data)
        self.msg_thread.start()
        self.data_thread.start()

        self.initUI()
        self.console.append(
            f"Listening for messages on port {self.msg_port}...")
        self.console.append(
            f"Listening for data on port {self.data_port}...")

    def initUI(self):
        self.setWindowTitle(window_title)

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

        self.stream_button = QPushButton("Stream", self)
        self.stream_button.clicked.connect(self.stream_cb)

        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.record_cb)

        self.max_record_time_label = QLabel("Max record time", self)
        self.max_record_time_spin_box = QSpinBox(self)
        self.max_record_time_spin_box.setSuffix(" s")
        self.max_record_time_spin_box.setRange(0, 3600)
        self.max_record_time_spin_box.setValue(self.max_record_time)
        self.max_record_time_spin_box.setEnabled(True)

        self.timer_spin_box = QSpinBox(self)
        self.timer_spin_box.setSuffix(" s")
        self.timer_spin_box.setRange(0, 3600)
        self.timer_spin_box.setValue(self.timer)

        self.timer_checkbox = QCheckBox("Timed recording", self)
        self.timer_checkbox.setChecked(True)
        self.timer_checkbox.stateChanged.connect(
            self.timer_spin_box.setEnabled)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

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

        self.console = QTextEdit(self)
        self.console.setReadOnly(True)

        # MultiGraph
        if self.zero:
            y_label = (f"I{sub('ds')}", "A")
        else:
            y_label = (f"&Delta;I{sub('ds')}", "A")

        self.multi_graph = MultiGraph(
            self.n_channels,
            self.fs,
            self.time_range,
            ("Time", "s"),
            y_label
        )

        self.recording_time_label = QLabel("[00:00:00]", self)
        self.clear_plot_button = QPushButton("Clear plot", self)
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.pause_streaming_button = QPushButton("Pause", self)
        self.pause_streaming_button.setEnabled(False)
        self.pause_streaming_button.clicked.connect(self.pause_stream)

        # Sample rate
        self.sample_rate_label = QLabel("Sample rate", self)
        self.sample_rate_combo = QComboBox(self)
        self.sample_rate_combo.addItems(
            [khertz2string(f) for f in self.sample_rates])
        self.sample_rate_combo.setCurrentIndex(
            self.sample_rates.index(self.fs)
        )
        self.sample_rate_combo.currentIndexChanged.connect(
            self.update_sample_rate)

        # Time range
        self.time_range_label = QLabel("Time range", self)
        self.time_range_combo = QComboBox(self)
        self.time_range_combo.addItems(
            [s2string(t) for t in self.time_ranges])
        self.time_range_combo.setCurrentIndex(
            self.time_ranges.index(self.time_range)
        )
        self.time_range_combo.currentIndexChanged.connect(
            self.update_time_range)

        self.layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.rec_groupbox = QGroupBox("Recording")

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.record_button)
        self.button_layout.addWidget(self.stream_button)

        self.timer_layout = QHBoxLayout()
        self.timer_layout.addWidget(self.timer_checkbox)
        self.timer_layout.addWidget(self.timer_spin_box)
        self.timer_layout.addWidget(self.max_record_time_label)
        self.timer_layout.addWidget(self.max_record_time_spin_box)

        self.group_boxes = {}
        for i in range(self.n_channels):
            self.group_boxes[i] = QGroupBox(f"Channel {i+1} settings")

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
            self.left_layout.addWidget(self.group_boxes[i])

        self.tag_layout = QHBoxLayout()
        self.tag_layout.addWidget(self.tag_line_edit)
        self.tag_layout.addWidget(self.tag_button)
        self.rec_layout = QVBoxLayout()
        self.rec_layout.addLayout(self.button_layout)
        self.rec_layout.addWidget(self.name_line_edit)
        self.rec_layout.addLayout(self.tag_layout)
        self.rec_layout.addLayout(self.timer_layout)
        self.rec_groupbox.setLayout(self.rec_layout)
        self.left_layout.addWidget(self.rec_groupbox)
        self.left_layout.addWidget(self.console)

        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.multi_graph)
        self.time_layout = QHBoxLayout()
        self.time_layout.addStretch()
        self.time_layout.addWidget(self.clear_plot_button)
        self.time_layout.addWidget(self.pause_streaming_button)
        self.time_layout.addWidget(self.sample_rate_label)
        self.time_layout.addWidget(self.sample_rate_combo)
        self.time_layout.addWidget(self.time_range_label)
        self.time_layout.addWidget(self.time_range_combo)
        self.time_layout.addWidget(self.recording_time_label)
        self.right_layout.addLayout(self.time_layout)

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)
        self.layout.setStretch(1, 4)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def start_timer(self):
        self.timer.start(1000)

    def pause_timer(self):
        self.timer.stop()

    def stop_timer(self):
        self.timer.stop()
        self.elapsed_time = 0
        self.recording_time_label.setText("[00:00:00]")

    def update_timer(self):
        self.elapsed_time += 1
        self.recording_time_label.setText(f"[{s2hhmmss(self.elapsed_time)}]")

        if self.timer_checkbox.isChecked():
            if self.elapsed_time >= self.timer_spin_box.value():
                self.stop_timer()
                self.stream_cb()
            elif self.elapsed_time % self.max_record_time_spin_box.value() == 0:
                self.stream_cb()
                self.record_cb()
        else:
            if self.elapsed_time % self.max_record_time_spin_box.value() == 0:
                self.stream_cb()
                self.record_cb()

    def send_command(self, command):
        self.msg_socket.sendto(command.encode(), self.server_address)

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

    def send_user_command(self):
        command = self.line_edit.toPlainText()
        self.send_command(command)

    def record_cb(self):
        if not self.recording:  # Start recording
            self.start_timer()
            name = "data"
            if self.name_line_edit.text() != "":
                name = self.name_line_edit.text()
            self.send_command("rec " + name)
            self.recording = True
            self.record_button.setText("Pause")
            self.tag_button.setEnabled(True)
            if not self.streaming:  # Start streaming
                self.data_thread.listening = True
                self.streaming = True
                self.pause_streaming_button.setEnabled(True)
            self.stream_button.setText("Save")
            self.name_line_edit.setEnabled(False)
        else:  # Stop recording
            if not self.paused:  # Pause recording
                self.pause_timer()
                self.send_command("pause")
                self.paused = True
                self.record_button.setText("Resume")
                self.tag_button.setEnabled(False)
            else:  # Resume recording
                self.start_timer()
                self.send_command("resume")
                self.paused = False
                self.record_button.setText("Pause")
                self.tag_button.setEnabled(True)

    def stream_cb(self):
        if not self.streaming:  # Start streaming
            self.data_thread.listening = True
            self.send_command("start")
            self.streaming = True
            self.stream_button.setText("Stop")
            self.pause_streaming_button.setEnabled(True)
        else:  # Stop streaming
            self.data_thread.listening = False
            self.send_command("stop")
            self.streaming = False
            self.stream_button.setText("Stream")
            if self.recording or self.paused:  # If recording, stop it
                self.pause_timer()
                self.recording = False
                self.paused = False
                self.record_button.setText("Record")
                self.name_line_edit.setEnabled(True)
            self.tag_button.setEnabled(False)
            self.pause_streaming_button.setEnabled(False)

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
        points = bytes2samples(data, self.zero)
        self.multi_graph.update_scrolls(points)

    def clear_plot(self):
        self.multi_graph.clear_scrolls()

    def pause_stream(self):
        if self.data_thread.listening:
            self.data_thread.listening = False
            self.pause_streaming_button.setText("Resume")
        else:
            self.data_thread.listening = True
            self.pause_streaming_button.setText("Pause")

    def update_time_range(self, index):
        self.time_range = self.time_ranges[index]
        self.data_thread.update_bytes_to_emit(self.fs, self.time_range)
        self.multi_graph.init_data(self.fs, self.time_range)

    def update_sample_rate(self, index):
        self.fs = self.sample_rates[index]
        self.T2 = float(1e6/self.fs)
        self.multi_graph.init_data(self.fs, self.time_range)

        self.send_command(f"sT2 {self.T2}")

    def closeEvent(self, event):
        # self.send_command("stop")
        self.msg_thread.terminate()
        self.data_thread.terminate()
        self.msg_socket.close()
        self.data_socket.close()
        event.accept()
