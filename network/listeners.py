from collections import deque

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


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
                self.msg, _ = self.socket.recvfrom(self.msg_len)
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

    def set_bytes_to_emit(self, n_bytes):
        self.bytes_to_emit = int(n_bytes)
        self.data_buffer = deque(maxlen=self.bytes_to_emit)

    def run(self):
        while True:
            if self.listening:
                data, _ = self.socket.recvfrom(self.BUF_LEN)
                self.data_buffer.extend(data)
                # print data in hex format
                # print(" ".join("{:02x}".format(x) for x in data))

                if len(self.data_buffer) >= self.bytes_to_emit:
                    self.received_data.emit(np.array(self.data_buffer))
                    self.data_buffer.clear()

    def start_listening(self):
        self.listening = True

    def stop_listening(self):
        self.listening = False
