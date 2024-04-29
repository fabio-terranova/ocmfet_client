"""
This file contains the default values for the configuration of the application.
default_z is used to overwrite the default values when the zero flag is passed,
which is used to run the non-feedback version of the app.
Also contains the config_pyqtgraph function to configure the pyqtgraph library.
"""
import pyqtgraph as pg

version = "2.4"
author = "Fabio Terranova"

# Default values for the feedback version of the device
default = {
    "win_title": "OCMFET client {} - {}".format(version, author),
    "zero": False,
    "server_ip": "192.168.137.240",
    "msg_port": 8888,
    "data_port": 8889,
    "ch_layout": [(1, 1), (2, 1)],  # layout of the channels
    "T2": 44,  # us
    "BUF_LEN": 32,  # bytes
    "sample_rates": [5, 10, 20, 30, 40, 50],  # kHz
    "sample_rate": 20,  # kHz
    "time_ranges": [1, 10, 30, 60],  # seconds
    "time_range": 10,  # seconds
    "timer": 600,  # seconds
    "max_record_time": 300,  # seconds
    "bandpass": [(10, 5e3), 2],  # Hz, order
    "notch": [50, 20],  # Hz, Q-factor
}

# Default values for the non-feedback version (zero) of the device (overwrites the default)
default_z = {
    "win_title": "OCMFET client {} - {} (zero)".format(version, author),
    "zero": True,
    "server_ip": "192.168.137.240",
    "T2": 200,  # us
    "BUF_LEN": 6,  # bytes
    "sample_rate": 5,  # kHz
}


def config_pyqtgraph():
    """
    Configures the pyqtgraph library
    """
    # pg.setConfigOptions(useOpenGL=True)
    # pg.setConfigOption('antialias', True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
