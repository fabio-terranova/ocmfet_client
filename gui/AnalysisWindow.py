from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QVBoxLayout, QWidget

from gui.widgets.MultiGraph import MultiGraphWidget
from network.listeners import DataReader
from utils.processing import DataProcessor


class AnalysisWindow(QMainWindow):
    def __init__(self, title, config):
        super().__init__()

        self.win_title = title
        self.channels = config["channels"]
        self.fs = config["sample_rate"]
        self.tr = config["time_range"]

        self.data_processor = DataProcessor(len(self.channels), self.fs, self.tr)

        self.data_reader = DataReader(self)
        self.data_reader.data_read.connect(self.update_data)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.win_title)
        self.setMinimumSize(500, 500)

        self.multi_graph = MultiGraphWidget(self.channels, self.fs, self.tr, self)

        self.load_button = QPushButton("Load file")
        self.load_button.clicked.connect(self.load_file)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.multi_graph)
        self.layout.addWidget(self.load_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def update_data(self, data):
        self.data_processor.update_data(data)
        self.multi_graph.update_curves(self.data_processor.get_data())

    def load_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Load file", None, "Binary files (*.bin)"
        )

        if file:
            with open(file, "rb") as f:
                f_size = f.seek(0, 2)
                f.seek(0, 0)
                time = f_size / 4 / self.fs / 1e3
                self.multi_graph.change_time_range(time)
                self.data_processor.change_max_time(time)

            self.data_reader.open_file(file)
