from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMainWindow, QPushButton,
                             QSpinBox, QStyle, QToolButton, QVBoxLayout,
                             QWidget)

from gui.Controller import ControllerDialog
from gui.Messanger import Messanger
from gui.PlotDialog import PlotDialog
from network.udp import MsgDataClient
from utils.formatting import s2hhmmss


class AcqWindow(QMainWindow):
    """
    Main window of the acquisition system.
    """

    def __init__(self, title, config):
        super().__init__()

        # Load configuration
        self.win_title = title
        self.server_ip = config["server_ip"]
        self.msg_port = config["msg_port"]
        self.data_port = config["data_port"]
        self.channels = config["channels"]
        self.n_channels = len(self.channels)
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

        self.udp_client = MsgDataClient(
            self.server_ip,
            self.msg_port,
            self.data_port,
            config["BUF_LEN"],
            200*self.n_channels*int(self.fs*self.time_range),
        )

        self.msg_widget = Messanger(
            config["commands"], self.udp_client, self
        )

        self.plot_dialog = PlotDialog(
            config,
            self.udp_client.data_listener,
            self
        )

        self.ocmfet_dialog = ControllerDialog(
            [ch for ch in self.channels if ch["type"] >= 1],
            self.udp_client,
            self
        )

        self.initUI()
        self.setGeometry(self.sizeHint().width(), 0, self.sizeHint().width(),
                         self.sizeHint().height())
        self.startup()

    def initUI(self):
        self.setWindowTitle(self.win_title)

        self.ocmfet_button = QPushButton("OCMFET controller", self)
        self.ocmfet_button.clicked.connect(self.ocmfet_dialog.show)
        self.ocmfet_button.setEnabled(
            any([True if ch["type"] >= 1 else False for ch in self.channels])
        )

        self.plot_button = QPushButton("Live plot", self)
        self.plot_button.clicked.connect(self.plot_dialog.show)

        self.record_button = QToolButton(self)
        self.record_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay))
        self.record_button.clicked.connect(self.record_cb)

        self.playpause_button = QToolButton(self)
        self.playpause_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPause))
        self.playpause_button.clicked.connect(self.pause_cb)
        self.playpause_button.setEnabled(False)

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
        self.recording_time_label = QLabel("Not recording", self)

        self.layout = QVBoxLayout()

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.ocmfet_button)
        self.buttons_layout.addWidget(self.plot_button)
        # self.buttons_layout.addWidget(self.data_button)
        self.layout.addLayout(self.buttons_layout)

        self.acq_groupbox = QGroupBox("Recording")
        self.acq_layout = QGridLayout()
        self.acq_layout.addWidget(self.name_line_edit, 0, 0, 1, 1)
        self.acq_layout.addWidget(self.record_button, 0, 1, 1, 1)
        self.acq_layout.addWidget(self.playpause_button, 0, 2, 1, 1)
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
        self.acq_layout.addLayout(self.tag_layout, 1, 0, 1, 3)
        self.acq_layout.addLayout(self.rec_layout, 2, 0, 1, 3)
        self.acq_layout.addLayout(self.time_layout, 3, 0, 1, 3)
        self.acq_groupbox.setLayout(self.acq_layout)
        self.layout.addWidget(self.acq_groupbox)

        self.layout.addWidget(self.msg_widget)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def startup(self):
        self.plot_dialog.show()
        self.udp_client.start_listening()
        self.send_command("start")
        self.send_command("stream")

    def start_timer(self):
        self.timer.start(1000)

    def pause_timer(self):
        self.timer.stop()

    def stop_timer(self):
        self.timer.stop()
        self.elapsed_time = 0
        self.recording_time_label.setText("Not recording")

    def update_timer(self):
        self.elapsed_time += 1
        if self.timer_checkbox.isChecked():
            self.recording_time_label.setText(
                f"{s2hhmmss(self.elapsed_time)}/{s2hhmmss(self.timer_spin_box.value())}")
        else:
            self.recording_time_label.setText(
                f"{s2hhmmss(self.elapsed_time)}")

        if self.timer_checkbox.isChecked():
            if self.elapsed_time >= self.timer_spin_box.value():
                self.stop_timer()
                self.record_cb()
            elif self.elapsed_time % self.max_record_time_spin_box.value() == 0:
                self.save_recording()
                self.send_command("rec")
        else:
            if self.elapsed_time % self.max_record_time_spin_box.value() == 0:
                self.save_recording()
                self.send_command("rec")

    def send_command(self, command):
        self.udp_client.send_message(command)

    def send_user_command(self):
        command = self.line_edit.toPlainText()
        self.send_command(command)

    def pause_cb(self):
        if self.recording:
            if not self.paused:  # Pause recording
                self.pause_timer()
                self.send_command("pause")
                self.paused = True

                self.playpause_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))
                self.tag_button.setEnabled(False)
            else:  # Resume recording
                self.start_timer()
                self.send_command("resume")
                self.paused = False

                self.playpause_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
                self.tag_button.setEnabled(True)

    def record_cb(self):
        if not self.recording:  # Start recording
            self.start_timer()
            self.send_command("rec")
            self.recording = True

            self.record_button.setIcon(
                self.style().standardIcon(QStyle.SP_DialogSaveButton))
            self.tag_button.setEnabled(True)
            self.playpause_button.setEnabled(True)
        else:  # Stop recording
            self.stop_timer()
            self.recording = False
            self.save_recording()

            self.record_button.setIcon(
                self.style().standardIcon(QStyle.SP_DialogNoButton))
            self.tag_button.setEnabled(False)
            self.playpause_button.setEnabled(False)

    def save_recording(self):
        name = "data"
        if self.name_line_edit.text() != "":
            name = self.name_line_edit.text()
        self.send_command("save " + name)

    def tag_cb(self):
        tag = self.tag_line_edit.text()
        if tag == "":
            tag = "tag"

        self.send_command(f"tag {tag}")

    def closeEvent(self, event):
        self.send_command("stop")
        self.udp_client.close()
        event.accept()
