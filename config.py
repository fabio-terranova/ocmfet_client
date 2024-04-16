# Description: Contains the default values for the configuration of the application.

# Default values for the feedback version of the device
default = {
    "zero": False,
    "server_ip": "192.168.137.240",
    "msg_port": 8888,
    "data_port": 8889,
    "T2": 44,  # us
    "BUF_LEN": 32,
    "n_channels": 2,
    "timer": 600,  # seconds
    "max_record_time": 300,  # seconds
    "sample_rates": [5, 10, 20, 30, 40, 50],  # kHz
    "sample_rate": 20,  # kHz
    "time_ranges": [1, 10, 30, 60],  # seconds
    "time_range": 10,  # seconds
}

# Default values for the non-feedback version (zero) of the device (overwrites the default)
default_z = {
    "zero": True,
    "server_ip": "192.168.137.240",
    "T2": 200,  # us
    "BUF_LEN": 6,
    "sample_rate": "5 kHz",
}
