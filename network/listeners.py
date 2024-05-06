import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

import oCPPmfet as oc


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
        self.converter = oc.Converter(self.bytes_to_emit // 2)

    def run(self):
        while True:
            if self.listening:
                data = self.socket.recv(self.BUF_LEN)

                if self.ptr < self.bytes_to_emit:
                    self.converter.append(data)
                    self.ptr += len(data)
                    # print data in hex format
                    # print(" ".join("{:02x}".format(x) for x in data))
                else:
                    points = self.converter.get_samples()
                    self.received_data.emit(points)
                    self.converter.clear()
                    self.ptr = 0

    def start_listening(self):
        self.listening = True

    def stop_listening(self):
        self.listening = False


class DataReader(QThread):
    data_read = pyqtSignal(np.ndarray)

    def __init__(self, file):
        super().__init__()
        self.file = file

    def run(self):
        with open(self.file, "rb") as f:
            f_size = f.seek(0, 2)
            f.seek(0, 0)
            self.data_buffer = oc.Converter(f_size // 2)
            for _ in range(0, f_size, 32):
                b = f.read(32)
                self.data_buffer.append(b)
            self.data_read.emit(self.data_buffer.get_samples())
