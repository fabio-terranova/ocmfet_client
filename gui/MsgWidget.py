from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)


class MsgWidget(QWidget):
    """
    MsgWidget class

    The widget allows the user to send commands to the server and visualize the response.

    Parameters
    ----------
    commands : dict
        Dictionary with the commands and their label, e.g., {"run": "Run", ...}

    udp_client : UDPClient
        UDP client object
    """

    def __init__(self, commands, udp_client, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.commands = commands
        self.udp_client = udp_client
        self.is_connected = False
        self.init_ui()

    def init_ui(self):
        self.console = QTextEdit(self)
        font = QFont()
        font.setFamily("Courier")
        self.console.setFont(font)
        self.console.setReadOnly(True)

        # Add lineEdit with send button
        self.command_line = QLineEdit(self)
        self.cmd_combo = QComboBox(self)
        self.cmd_combo.addItems(self.commands.values())
        self.cmd_combo.activated.connect(lambda i: self.command_line.setText(
            list(self.commands.keys())[i]))
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setDefault(True)
        self.command_line.returnPressed.connect(self.send_command)
        self.command_layout = QHBoxLayout()
        self.command_layout.addWidget(self.command_line)
        self.command_layout.addWidget(self.cmd_combo)
        self.command_layout.addWidget(self.send_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.console)
        self.layout.addLayout(self.command_layout)
        self.setLayout(self.layout)

        self.connect()
        self.console.append("Listening for messages on port {}.".format(
            self.udp_client.msg_port))
        self.console.append("Listening for data on port {}.".format(
            self.udp_client.data_port))

    def send_command(self):
        """ Send command to the server."""
        cmd = self.command_line.text()
        if bool(cmd):
            self.udp_client.send_message(cmd)
            self.console.append(f"[client] {cmd}")
            self.command_line.clear()

    def update_console(self, msg):
        """ Update the console with the received message."""
        log = f"[server] {msg}"
        self.console.append(log)

    def connect(self):
        """ Connect the UDP client."""
        self.udp_client.msg_listener.received_msg.connect(
            self.update_console)
        self.is_connected = True

    def disconnect(self):
        """ Disconnect the UDP client."""
        self.udp_client.msg_listener.received_msg.disconnect(
            self.update_console)
        self.is_connected = False
