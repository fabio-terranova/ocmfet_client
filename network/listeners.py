from collections import deque

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

import oCPPmfet as oc
from utils.processing import bytes2samples

class MessageListener(QThread):
    received_msg = pyqtSignal(str)

    def __init__(self, msg_socket, msg_len):
        super().__init__()
        self.socket = msg_socket
        self.msg_len = msg_len
        self.listening = True

    def run(self):
        while True:
            if self.listening:
                self.msg = self.socket.recv(self.msg_len)
                self.received_msg.emit(self.msg.decode())

    def start_listening(self):
        self.listening = True

    def stop_listening(self):
        self.listening = False


class DataListener(QThread):
    received_data = pyqtSignal(np.ndarray)

    def __init__(self, data_socket, BUF_LEN, bytes_to_emit):
        super().__init__()
        self.socket = data_socket
        self.BUF_LEN = BUF_LEN
        self.set_bytes_to_emit(bytes_to_emit)
        self.listening = False
        self.ptr = 0

    def set_bytes_to_emit(self, n_bytes):
        self.bytes_to_emit = int(n_bytes)
        # self.data_buffer = deque(maxlen=self.bytes_to_emit)
        self.converter = oc.Converter(self.bytes_to_emit // 2)

    def run(self):
        while True:
            if self.listening:
                data = self.socket.recv(self.BUF_LEN)

                if self.ptr < self.bytes_to_emit:
                    self.converter.append(data)
                    self.ptr += len(data)
                else:
                    points = self.converter.get_samples()
                    self.received_data.emit(points)
                    self.converter.clear()
                    self.ptr = 0

                # self.data_buffer.extend(data)
                # # print data in hex format
                # # print(" ".join("{:02x}".format(x) for x in data))

                # if len(self.data_buffer) >= self.bytes_to_emit:
                #     self.received_data.emit(np.array(self.data_buffer))
                #     self.data_buffer.clear()

    def start_listening(self):
        self.listening = True

    def stop_listening(self):
        self.listening = False


class DataReader(QThread):
    data_read = pyqtSignal(np.ndarray)

    def __init__(self, parent):
        super().__init__(parent)
        self.data_buffer = deque()

    def open_file(self, file):
        with open(file, "rb") as f:
            f_size = f.seek(0, 2)
            chunk_size = f_size // 32
            f.seek(0, 0)
            for i in range(0, f_size, chunk_size):
                b = f.read(chunk_size)
                self.data_buffer.extend(b)
                points = bytes2samples(np.array(self.data_buffer))
                self.data_read.emit(points)
        self.data_buffer.clear()
