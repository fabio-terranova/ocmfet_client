from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMainWindow, QPushButton,
                             QSpinBox, QVBoxLayout, QWidget)

from gui.ControllerWidget import ControllerDialog
from gui.MsgWidget import MsgWidget
from gui.PlotDialog import PlotDialog
from network.udp_client import UDPMsgDataClient
from utils.formatting import s2hhmmss


class MainWindow(QMainWindow):
    """
    Main window of the UDP client.
    """

    def __init__(self, config):
        super().__init__()

        # Load configuration
        self.win_title = config["win_title"]
        self.zero = config["zero"]
        self.server_ip = config["server_ip"]
        self.msg_port = config["msg_port"]
        self.data_port = config["data_port"]
        self.ch_layout = config["ch_layout"]
        self.n_channels = len(self.ch_layout)
        self.T2 = config["T2"]
        self.time_ranges = config["time_ranges"]
        self.sample_rates = config["sample_rates"]
        self.fs = config["sample_rate"]
        self.time_range = config["time_range"]
        self.timer = config["timer"]
        self.max_record_time = config["max_record_time"]
        self.bandpass = config["bandpass"]
        self.notch = config["notch"]

        # Status flags
        self.recording = False
        self.paused = False
        self.streaming = False

        self.udp_client = UDPMsgDataClient(
            self.server_ip,
            self.msg_port,
            self.data_port,
            config["BUF_LEN"],
            int(128*self.fs*self.time_range),
        )
        self.udp_client.start_listening()

        self.msg_widget = MsgWidget({
            "start": "Start acquisition",
            "stop": "Stop acquisition",
        }, self.udp_client, self)

        self.plot_dialog = PlotDialog(
            config,
            self.udp_client.data_listener,
            self
        )

        self.ocmfet_dialog = ControllerDialog(
            self.ch_layout,
            self.udp_client,
            self.zero,
            self
        )

        self.initUI()
        self.setGeometry(100, 100, self.sizeHint().width(),
                         self.sizeHint().height())
        self.plot_dialog.show()

    def initUI(self):
        self.setWindowTitle(self.win_title)

        self.ocmfet_button = QPushButton("OCMFET controller", self)
        self.ocmfet_button.clicked.connect(self.ocmfet_dialog.show)

        self.plot_button = QPushButton("Live plot", self)
        self.plot_button.clicked.connect(self.plot_dialog.show)

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

        # Recording time
        self.recording_time_label = QLabel("[00:00:00]", self)

        self.layout = QVBoxLayout()

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.ocmfet_button)
        self.buttons_layout.addWidget(self.plot_button)
        self.layout.addLayout(self.buttons_layout)

        self.acq_groupbox = QGroupBox("Acquisition")
        self.acq_layout = QVBoxLayout()
        self.acq_layout.addWidget(self.stream_button)
        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(self.name_line_edit)
        self.name_layout.addWidget(self.record_button)
        self.tag_layout = QHBoxLayout()
        self.tag_layout.addWidget(self.tag_line_edit)
        self.tag_layout.addWidget(self.tag_button)
        self.rec_layout = QGridLayout()
        self.rec_layout.addWidget(self.timer_checkbox, 0, 0)
        self.rec_layout.addWidget(self.timer_spin_box, 0, 1)
        self.rec_layout.addWidget(self.max_record_time_label, 1, 0)
        self.rec_layout.addWidget(self.max_record_time_spin_box, 1, 1)
        self.time_layout = QHBoxLayout()
        self.time_layout.addStretch()
        self.time_layout.addWidget(self.recording_time_label)
        self.acq_layout.addLayout(self.name_layout)
        self.acq_layout.addLayout(self.tag_layout)
        self.acq_layout.addLayout(self.rec_layout)
        self.acq_layout.addLayout(self.time_layout)
        self.acq_groupbox.setLayout(self.acq_layout)
        self.layout.addWidget(self.acq_groupbox)

        self.layout.addWidget(self.msg_widget)

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
        self.udp_client.send_message(command)

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
                self.udp_client.data_listener.start_listening()
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
            self.udp_client.data_listener.start_listening()
            self.send_command("start")
            self.streaming = True
            self.stream_button.setText("Stop")
            self.plot_dialog.pause_button.setEnabled(True)
        else:  # Stop streaming
            self.udp_client.data_listener.stop_listening()
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
            self.plot_dialog.pause_button.setEnabled(False)

    def tag_cb(self):
        tag = self.tag_line_edit.text()
        if tag == "":
            tag = "tag"

        self.send_command(f"tag {tag}")

    def update_console(self, msg):
        log = f"[{self.server_ip}]: {msg}"
        self.console.append(log)

    def closeEvent(self, event):
        # self.send_command("stop")
        self.udp_client.close()
        event.accept()

    def moveEvent(self, event):
        if self.plot_dialog.isVisible() and self.plot_dialog.glued_checkbox.isChecked():
            self.plot_dialog.move(self.x() + self.width(), self.y())
        event.accept()
