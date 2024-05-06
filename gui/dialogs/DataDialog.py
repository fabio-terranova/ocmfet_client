import json
import os

import numpy as np
import pandas as pd
from PyQt5.QtCore import QSize, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QProgressDialog,
    QTreeView,
    QVBoxLayout,
)

from utils.formatting import bytes2samples


class Downloader(QThread):
    progress = pyqtSignal(int)

    def __init__(self, udp_client):
        super().__init__()
        self.udp_client = udp_client
        self.size_counter = 0
        self.file_size = 0
        self.old_bytes_to_emit = self.udp_client.data_listener.bytes_to_emit

    def download_data(self, name, path, size):
        file_name, _ = QFileDialog.getSaveFileName(
            self.parent(), "Save file", name + ".csv", "All files (*)"
        )
        if file_name:
            if os.path.exists(file_name):
                os.remove(file_name)
            pd.DataFrame(columns=["Ch. 1", "Ch. 2"]).to_csv(
                file_name, index=False, header=True
            )
            self.file_size = size
            self.udp_client.data_listener.set_bytes_to_emit(int(size / 32))
            self.udp_client.data_listener.start_listening()
            self.udp_client.send_message("getf {}".format(path))
            self.udp_client.data_listener.received_data.connect(
                lambda data: self.write_to_file(file_name, data)
            )

    def stop_download(self):
        self.udp_client.data_listener.stop_listening()
        self.udp_client.data_listener.set_bytes_to_emit(self.old_bytes_to_emit)
        self.udp_client.data_listener.received_data.disconnect()

    def write_to_file(self, file_name, data):
        with open(file_name, "ab") as file:
            # write to csv file
            new_data = np.frombuffer(data, dtype=np.uint8)
            new_data = [bytes2samples(new_data[::2]), bytes2samples(new_data[1::2])]
            pd.DataFrame(new_data).to_csv(file, index=False, header=False, mode="a")

        self.size_counter += len(data)
        self.progress.emit(self.size_counter)
        print(self.size_counter, self.file_size)
        if self.size_counter >= self.file_size:
            self.stop_download()


class DataDialog(QDialog):
    def __init__(self, udp_client, parent=None):
        super().__init__(parent)
        self.udp_client = udp_client
        self.downloader = Downloader(udp_client)
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
