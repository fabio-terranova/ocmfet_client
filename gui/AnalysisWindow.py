from PyQt5.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QPushButton,
    QGridLayout,
    QWidget,
    QComboBox,
    QLabel,
)
from PyQt5.QtCore import Qt

from gui.widgets.MultiGraph import MultiGraphWidget
from network.listeners import DataReader
from utils.processing import DataProcessor

import os


class AnalysisWindow(QMainWindow):
    def __init__(self, title, config):
        super().__init__()

        self.win_title = title
        self.channels = config["channels"]
        self.fs = config["sample_rate"]
        self.tr = config["time_range"]

        self.data_processor = DataProcessor(len(self.channels), self.fs, self.tr)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.win_title)
        self.setMinimumSize(500, 500)

        self.name_label = QLabel("Select a folder")
        self.name_label.setStyleSheet("font-weight: bold")
        self.name_label.setAlignment(Qt.AlignmentFlag(4))

        self.multi_graph = MultiGraphWidget(self.channels, self.fs, self.tr, self)

        self.files_label = QLabel("Files: ")
        self.files_combo = QComboBox()
        self.files_combo.activated.connect(self.update_file)

        self.open_folder_button = QPushButton("Open folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_file_button = QPushButton("Open file")
        self.open_file_button.clicked.connect(self.open_file)

        self.layout = QGridLayout()
        self.layout.setColumnStretch(1, 1)
        self.layout.addWidget(self.name_label, 0, 0, 1, 4)
        self.layout.addWidget(self.multi_graph, 1, 0, 1, 4)
        self.layout.addWidget(self.files_label, 2, 0, 1, 1)
        self.layout.addWidget(self.files_combo, 2, 1, 1, 1)
        self.layout.addWidget(self.open_folder_button, 2, 2, 1, 1)
        self.layout.addWidget(self.open_file_button, 2, 3, 1, 1)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def update_data(self, data):
        self.data_processor.update_data(data)
        self.multi_graph.update_curves(self.data_processor.get_data())

    def update_file(self, idx):
        file = self.files_combo.itemText(idx)
        f_name = os.path.basename(file)
        self.name_label.setText(f_name)

        with open(file, "rb") as f:
            f_size = f.seek(0, 2)
            f.seek(0, 0)
            time = f_size / 4 / self.fs / 1e3
            self.multi_graph.change_time_range(time)
            self.data_processor.change_max_time(time)

        self.data_reader = DataReader(file)
        self.data_reader.data_read.connect(self.update_data)
        self.data_reader.run()

    def open_folder(self):
        # Open file dialog
        folder = QFileDialog.getExistingDirectory(self, "Open folder")

        if folder:
            files = [
                os.path.join(folder, file)
                for file in os.listdir(folder)
                if file.endswith(".bin")
            ]
            self.files_combo.clear()
            self.files_combo.addItems(files)
            self.files_combo.setCurrentIndex(0)
            self.update_file(0)

    def open_file(self):
        # Open file dialog
        file, _ = QFileDialog.getOpenFileName(
            self, "Open file", "", "Binary files (*.bin)"
        )

        if file:
            self.files_combo.addItem(file)
            self.files_combo.setCurrentIndex(self.files_combo.count() - 1)
            self.update_file(self.files_combo.count() - 1)
