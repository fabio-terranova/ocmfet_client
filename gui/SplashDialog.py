import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton

from gui.AnalysisWindow import AnalysisWindow
from gui.ConfigDialog import ConfigDialog
from gui.LiveWindow import LiveWindow


class SplashDialog(QDialog):
    """
    SplashDialog class
    """

    def __init__(self, version, title="Splash"):
        super().__init__()
        self.setWindowTitle(title)
        self.version = version
        self.selected = None
        self.config = yaml.safe_load(open("configs/default.yaml", "r"))
        self.init_ui()

    def init_ui(self):
        self.label = QLabel(
            "OCMFET multi-channel acquisition system\n\nSelect an option:"
        )
        self.version = QLabel(f"v{self.version}")
        self.version.setAlignment(Qt.AlignRight)
        self.label.setAlignment(Qt.AlignCenter)
        self.acq_btn = QPushButton(
            "Live acquisition", clicked=self.open_live)
        self.analysis_btn = QPushButton(
            "Offline analysis", clicked=self.open_analysis)
        self.config_btn = QPushButton(
            "Configuration", clicked=self.open_config)

        self.layout = QGridLayout()
        self.layout.addWidget(self.label, 0, 0, 1, 3)
        self.layout.addWidget(self.acq_btn, 1, 1)
        self.layout.addWidget(self.analysis_btn, 2, 1)
        self.layout.addWidget(self.config_btn, 3, 1)
        self.layout.addWidget(self.version, 4, 2)

        self.setLayout(self.layout)

    def open_config(self):
        config_dialog = ConfigDialog(self.config)
        if config_dialog.exec_() == QDialog.Accepted:
            self.config = config_dialog.config

    def open_live(self):
        self.selected = LiveWindow("Live acquisition", self.config)
        self.accept()

    def open_analysis(self):
        self.selected = AnalysisWindow("Data analysis", self.config)
        self.accept()
