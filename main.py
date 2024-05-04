"""
Fabio Terranova - 2023

Client for the OCMFET acquisition system developed by Elbatech

TODO
----
- Add offline data plotting
    - Local data
    - Remote data (server)
"""
import sys

import pyqtgraph as pg
import yaml
from PyQt5.QtWidgets import QApplication, QDialog

from gui.SplashDialog import SplashDialog

__version__ = "2.5"
author = "Fabio Terranova"

win_title = "OCMFET client - {}".format(author)


def config_pyqtgraph():
    """
    PyQtGraph configuration
    """
    pg.setConfigOptions(**{
        # 'useOpenGL': True,
        # 'antialias': True,
        'background': 'w',
        'foreground': 'k',
        'leftButtonPan': False,
    })


if __name__ == '__main__':
    # Configure PyQtGraph
    config_pyqtgraph()

    # Run Qt GUI
    app = QApplication([])
    splash = SplashDialog(version=__version__, title=win_title)

    # Usage main.py [-acq] [-off] [-c <config_file>]
    main = None
    if len(sys.argv) > 1:
        if "-c" in sys.argv:
            idx = sys.argv.index("-c")
            config_file = sys.argv[idx + 1]
            splash.config = yaml.safe_load(open(config_file, "r"))

        if "-l" in sys.argv:
            splash.open_acq()
        elif "-o" in sys.argv:
            splash.open_plot()
        main = splash.selected
    else:
        if splash.exec_() == QDialog.Accepted:
            main = splash.selected

    if main:
        main.show()
        app.exec_()
