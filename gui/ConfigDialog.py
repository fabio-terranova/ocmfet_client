import yaml
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QGridLayout,
                             QPushButton, QTabWidget, QTextEdit, QWidget)


class ConfigDialog(QDialog):
    """
    ConfigDialog class

    The dialog allows the user to load a configuration file. The user can run the application
    with the default configuration or load a custom configuration.
    The default configuration is defined in the default.yaml file in the configs folder.

    Parameters
    ----------
    parent : QWidget
        Parent widget
    """

    def __init__(self, default, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration editor")
        self.config = self.default = default
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.default_tab = QWidget()
        self.custom_tab = QWidget()
        self.tabs.addTab(self.default_tab, "Default")
        self.tabs.addTab(self.custom_tab, "Custom")

        self.def_text = QTextEdit()
        self.def_text.setFont(QFont("Courier New", 10))
        self.def_text.setPlainText(
            yaml.dump(self.config, default_flow_style=None, sort_keys=False, width=50))
        self.def_text.setReadOnly(True)
        self.def_text.setEnabled(False)
        self.def_text.setLineWrapMode(QTextEdit.NoWrap)
        self.def_text.setVerticalScrollBarPolicy(1)
        self.def_text.setHorizontalScrollBarPolicy(1)
        self.def_text.setMinimumWidth(int(self.def_text.document().size().width()))
        self.config_text = QTextEdit()
        self.config_text.setFont(QFont("Courier New", 10))
        self.config_text.setPlainText(
            yaml.dump(self.config, default_flow_style=None, sort_keys=False, width=50))
        self.config_text.setLineWrapMode(QTextEdit.NoWrap)

        self.default_tab.setLayout(QGridLayout())
        self.custom_tab.setLayout(QGridLayout())

        self.default_tab.layout().addWidget(self.def_text, 0, 0)
        self.default_tab.layout().addWidget(
            QPushButton("Use", clicked=self.use_def), 1, 0)

        self.custom_tab.layout().addWidget(self.config_text, 0, 0, 1, 3)
        self.custom_tab.layout().addWidget(
            QPushButton("Load", clicked=self.load_config), 1, 0)
        self.custom_tab.layout().addWidget(
            QPushButton("Save", clicked=self.save_config), 1, 1)
        self.custom_tab.layout().addWidget(
            QPushButton("Use", clicked=self.use), 1, 2)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self.tabs, 0, 0)

    def use_def(self):
        self.config = self.default
        self.accept()

    def use(self):
        self.config = yaml.safe_load(self.config_text.toPlainText())
        self.accept()

    def save_config(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save configuration", "configs", "YAML files (*.yaml)")
        if file:
            with open(file, "w") as f:
                f.write(self.config_text.toPlainText())

    def update_config(self):
        self.config_text.setPlainText(
            yaml.dump(self.config, default_flow_style=None, sort_keys=False, width=50))

    def load_config(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Load configuration", "configs", "YAML files (*.yaml)")
        if file:
            self.config = yaml.safe_load(open(file, "r"))
            self.update_config()


if __name__ == '__main__':
    app = QApplication([])
    dialog = ConfigDialog({"key": "value"})
    if dialog.exec_() == QDialog.Accepted:
        print(dialog.config)
