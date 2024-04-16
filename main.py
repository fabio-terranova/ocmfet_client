# Fabio Terranova - 2023
# Client for the OCMFET acquisition system developed by Elbatech
# TODO: add spectrum visualization for each channel

import sys

import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication

from config import default, default_z
from gui.main_window import UDPClientGUI

# pg.setConfigOptions(useOpenGL=True)
pg.setConfigOption('antialias', True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

version = "2.0"
window_title = f"OCMFET client {version} - Fabio Terranova"


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

    client = UDPClientGUI(default)

    client.show()
    sys.exit(app.exec_())
