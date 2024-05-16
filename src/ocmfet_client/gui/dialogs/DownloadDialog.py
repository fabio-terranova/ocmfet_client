import json

from PyQt5.QtCore import QSize, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QDialog,
    QProgressDialog,
    QTreeView,
    QVBoxLayout,
)

from network.udp import MsgDataClient


class Downloader(QThread):
    progress = pyqtSignal(int)

    def __init__(self, udp_client):
        super().__init__()
        self.udp_client = udp_client
        self.size_counter = 0
        self.file_size = 0
        self.old_bytes_to_emit = self.udp_client.data_listener.bytes_to_emit


class DownloadDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.server_ip = config["server_ip"]
        self.msg_port = config["msg_port"]
        self.data_port = config["data_port"]
        self.udp_client = MsgDataClient(
            self.server_ip, self.msg_port, self.data_port, config["BUF_LEN"]
        )
        self.downloader = Downloader(self.udp_client)
        self.json_string = ""
        self.columns = ["Name", "Duration", "Last modified"]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Data dialog")
        self.resize(QSize(500, 400))
        self.layout = QVBoxLayout()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.columns)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSortingEnabled(True)
        self.tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree.header().setSectionResizeMode(3)

        self.tree.doubleClicked.connect(self.double_click)

        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

    def double_click(self, index):
        if self.model.itemFromIndex(index).hasChildren():
            return

        # name and path of the selected row
        name = self.model.itemFromIndex(index.siblingAtColumn(0)).text()
        path = self.model.itemFromIndex(index.siblingAtColumn(4)).text()
        size = int(self.model.itemFromIndex(index.siblingAtColumn(3)).text())

        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setLabelText("Downloading {}".format(name))
        self.progress_dialog.setRange(0, size)
        self.downloader.download_data(name, path, size)
        self.downloader.progress.connect(self.progress_dialog.setValue)
        self.progress_dialog.exec_()

    def populate_tree(self, data):
        root_item = self.model.invisibleRootItem()
        self.json_string += data
        try:
            json.loads(self.json_string)
        except json.JSONDecodeError:
            return

        self.add_data_to_model(root_item, json.loads(self.json_string))

        for i in range(root_item.rowCount()):
            self.tree.setExpanded(self.model.index(i, 0), True)

    def add_data_to_model(self, item, data):
        for key, value in data.items():
            if isinstance(value, dict):
                parent = QStandardItem(key)
                item.appendRow(parent)
                self.add_data_to_model(parent, value)
            elif isinstance(value, list):
                items = [QStandardItem(str(key))]
                items.extend([QStandardItem(str(i)) for i in value])
                item.appendRow(items)

    def clear_model(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.columns)
        self.json_string = ""

    def showEvent(self, event):
        if self.parent():
            self.parent().msg_widget.disconnect()
            self.parent().plot_dialog.disconnect()
        self.udp_client.msg_listener.received_msg.connect(self.populate_tree)
        self.udp_client.send_message("data")
        event.accept()

    def closeEvent(self, event):
        if self.parent():
            self.parent().msg_widget.connect()
            self.parent().plot_dialog.connect()
        self.udp_client.msg_listener.received_msg.disconnect(self.populate_tree)
        self.clear_model()
        event.accept()
