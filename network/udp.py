import socket

from .listeners import DataListener, MessageListener


class MsgDataClient:
    def __init__(
        self, host, msg_port, data_port, data_len, bytes_to_emit=1024, msg_len=512
    ):
        self.host = host
        self.msg_port = msg_port
        self.data_port = data_port
        self.msg_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msg_socket.bind(("", self.msg_port))
        self.data_socket.bind(("", self.data_port))

        self.msg_listener = MessageListener(self.msg_socket, msg_len)
        self.data_listener = DataListener(self.data_socket, data_len, bytes_to_emit)

    def start_listening(self):
        self.msg_listener.start()
        self.data_listener.start()

    def send_message(self, msg):
        self.msg_socket.sendto(msg.encode(), (self.host, self.msg_port))

    def close(self):
        self.msg_listener.terminate()
        self.data_listener.terminate()
        self.msg_socket.close()
        self.data_socket.close()
