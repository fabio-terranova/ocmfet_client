import datetime
import time

import numpy as np


def size2string(data):
    """Convert size in bytes to string."""
    if data < 1e3:
        return f"{data:.0f} B"
    elif data < 1e6:
        return f"{data/1e3:.0f} kB"
    elif data < 1e9:
        return f"{data/1e6:.0f} MB"
    else:
        return f"{data/1e9:.0f} GB"


def datetime_range(n_samples, dt):
    """
    Returns a range of timestamps from now to now + dt.

    Parameters
    ----------
    n_samples : int
        Number of samples in the range.
    dt : float
        Time delta in seconds.
    """
    dt1 = datetime.datetime.now()
    dt2 = dt1 + datetime.timedelta(seconds=dt)
    return np.linspace(dt1.timestamp(), dt2.timestamp(), n_samples)


def htmlify(string):
    return f"<html>{string}</html>"


def mathify(string):
    return f"<math>{string}</math>"


def sub(string):
    return f"<sub>{string}</sub>"


def sup(string):
    return f"<sup>{string}</sup>"


def s2hhmmss(seconds):
    """Returns time in hh:mm:ss from seconds"""
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def string2ms(string):
    """Returns time in ms from string"""
    if string[-2:] == "ms":
        return int(float(string[:-3]))
    elif string[-3:] == "min":
        return int(float(string[:-4]) * 60e3)
    elif string[-1:] == "s":
        return int(float(string[:-2]) * 1e3)
    else:
        return int(string)


def s2string(s):
    """Returns string from time in seconds"""
    if s < 60:
        return f"{s:.0f} s"
    elif s < 3600:
        return f"{s/60:.0f} min"
    else:
        return f"{s/3600:.0f} h"


def ms2string(ms):
    """Returns string from time in ms"""
    if ms < 1e3:
        return f"{ms:.0f} ms"
    elif ms < 60e3:
        return f"{ms/1e3:.0f} s"
    else:
        return f"{ms/60e3:.0f} min"


def string2hertz(string):
    """Returns sample rate in Hz from string"""
    if string[-3:] == "kHz":
        return float(string[:-4]) * 1e3
    elif string[-3:] == "Hz":
        return float(string[:-3])
    else:
        return float(string)


def khertz2string(f):
    """Returns string from sample rate in kHz"""
    return f"{f:.0f} kHz"


def string2T(fs):
    """Returns period in us from string"""
    return float(1 / string2hertz(fs)) * 1e6
