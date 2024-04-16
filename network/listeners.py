from collections import deque

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class MessageListener(QThread):
    received_msg = pyqtSignal(str)

    def __init__(self, msg_socket):
        super().__init__()
        self.socket = msg_socket

    def run(self):
        while True:
            self.msg, _ = self.socket.recvfrom(512)
            self.received_msg.emit(self.msg.decode())


class DataListener(QThread):
    received_data = pyqtSignal(np.ndarray)

    def __init__(self, data_socket, sample_rate, time_range, BUF_LEN):
        super().__init__()
        self.listening = True
        self.socket = data_socket
        self.fs = sample_rate
        self.tr = time_range
        self.BUF_LEN = BUF_LEN
        self.update_bytes_to_emit(self.fs, self.tr)

    def update_bytes_to_emit(self, fs, tr):
        self.bytes_to_emit = int(128*fs*tr)
        # print(f"Bytes to emit: {self.bytes_to_emit}")
        self.data_buffer = deque(maxlen=self.bytes_to_emit)

    def run(self):
        while True:
            data, _ = self.socket.recvfrom(self.BUF_LEN)
            if self.listening:
                self.data_buffer.extend(data)

                if len(self.data_buffer) >= self.bytes_to_emit:
                    self.received_data.emit(np.array(self.data_buffer))
                    self.data_buffer.clear()
