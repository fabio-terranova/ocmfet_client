"""
This file contains the default app configuration.
"""

config = {
    # "server_ip": "193.43.20.240",
    "server_ip": "192.168.137.240",
    "msg_port": 8888,
    "data_port": 8889,
    "channels": [
        {
            "name": f"Ch. {n+1}",
            "coords": (i+1, j+1),
            "type": 1,
            "labels": {
                # "left": ("I<sub>ds</sub>", "A"),
                "left": ("&Delta;I<sub>ds</sub>", "A"),
                "bottom": ("Time", "s")
            }
        } for n, (i, j) in enumerate([(x, y) for x in range(2) for y in range(1)])
    ],
    "BUF_LEN": 32,  # bytes
    # "BUF_LEN": 6,  # bytes
    "sample_rates": [5, 10, 20, 30, 40, 50],  # kHz
    "sample_rate": 20,  # kHz
    "time_ranges": [1, 10, 30, 60],  # seconds
    "time_range": 1,  # seconds
    "timer": 600,  # seconds
    "max_record_time": 300,  # seconds
    "bandpass": [(10, 5e3), 2],  # Hz, order
    "notch": [50, 20],  # Hz, Q-factor
    "commands": {
        "start": "Start acquisition",
        "stop": "Stop acquisition",
        "stream": "Stream (on/off)",
        "rec": "Start recording",
        "save": "Save data",
        "pause": "Pause recording",
    }
}
