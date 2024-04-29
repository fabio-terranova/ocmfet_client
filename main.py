# Fabio Terranova - 2023
# Client for the OCMFET acquisition system developed by Elbatech

import sys

from PyQt5.QtWidgets import QApplication

from config import config_pyqtgraph, default, default_z
from gui.MainWindow import MainWindow

# Configure pyqtgraph
config_pyqtgraph()

if __name__ == '__main__':
    # Run Qt GUI
    app = QApplication(sys.argv)

    # Usage: client.py [-zero]
    zero = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "-zero":
            zero = True

    if zero:
        # Update default values
        default.update(default_z)

    client = MainWindow(default)
    client.show()
    sys.exit(app.exec_())
