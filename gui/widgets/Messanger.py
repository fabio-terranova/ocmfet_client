from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QShortcut,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class Messanger(QWidget):
    """
    Messanger class

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
        self.history = []
        self.history_index = 0
        self.init_ui()

    def init_ui(self):
        self.console = QTextEdit(self)
        font = QFont()
        font.setFamily("Courier")
        self.console.setFont(font)
        self.console.setReadOnly(True)
        self.console.setContextMenuPolicy(3)
        self.console.customContextMenuRequested.connect(self.console_menu)

        # Add lineEdit with send button
        self.command_line = QLineEdit(self)
        self.command_line.setPlaceholderText("Enter command")
        self.command_line.setFocus()
        self.command_line.setClearButtonEnabled(True)
        self.history_up = QShortcut("Up", self.command_line)
        self.history_down = QShortcut("Down", self.command_line)
        self.history_up.activated.connect(self.history_up_cmd)
        self.history_down.activated.connect(self.history_down_cmd)
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setDefault(True)
        self.command_line.returnPressed.connect(self.send_command)
        self.command_layout = QHBoxLayout()
        self.command_layout.addWidget(self.command_line)

        if self.commands:
            self.cmd_combo = QComboBox(self)
            self.cmd_combo.addItems(list(self.commands.values()))
            self.cmd_combo.activated[str].connect(
                lambda text: self.command_line.setText(
                    list(self.commands.keys())[list(self.commands.values()).index(text)]
                )
            )
            self.command_layout.addWidget(self.cmd_combo)

        self.command_layout.addWidget(self.send_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.console)
        self.layout.addLayout(self.command_layout)
        self.setLayout(self.layout)

        self.connect()

    def console_menu(self, pos):
        """Show context menu for the console."""
        menu = self.console.createStandardContextMenu()
        clear_action = menu.addAction("Clear")
        action = menu.exec_(self.console.viewport().mapToGlobal(pos))
        if action == clear_action:
            self.console.clear()

    def history_up_cmd(self):
        """Move up the command history."""
        if self.history:
            if self.history_index < len(self.history):
                self.history_index += 1
                self.command_line.setText(self.history[-self.history_index])

    def history_down_cmd(self):
        """Move down the command history."""
        if self.history:
            if self.history_index > 1:
                self.history_index -= 1
                self.command_line.setText(self.history[-self.history_index])
            else:
                self.history_index = 0
                self.command_line.clear()

    def send_command(self):
        """Send command to the server."""
        cmd = self.command_line.text()
        if bool(cmd):
            if len(self.history) > 0:
                if cmd != self.history[-1]:
                    self.history.append(cmd)
            else:
                self.history.append(cmd)

            self.history_index = 0
            self.udp_client.send_message(cmd)
            self.console.append(f"<b>client></b> {cmd}")
            self.command_line.clear()

    def update_console(self, msg):
        """Update the console with the received message."""
        log = f"<b style='color: #0000FF'>server></b> <i>{msg}</i>"
        self.console.append(log)

    def connect(self):
        """Connect the UDP client."""
        self.udp_client.msg_listener.received_msg.connect(self.update_console)
        self.is_connected = True

    def disconnect(self):
        """Disconnect the UDP client."""
        self.udp_client.msg_listener.received_msg.disconnect(self.update_console)
        self.is_connected = False
