import datetime
import time

import numpy as np


def bytes2samples(data, ch_type=2):
    """Convert bytes to samples."""
    if ch_type == 1:
        # 2Bytes(MSB2|MSB1)|2Bytes(LSW1)|2Bytes(LSW2)|...

        msb2 = np.array(data[0::6])
        msb1 = np.array(data[1::6])
        lsw1 = np.bitwise_or(
            np.left_shift(np.array(data[2::6]), 8), np.array(data[3::6])
        )
        lsw2 = np.bitwise_or(
            np.left_shift(np.array(data[4::6]), 8), np.array(data[5::6])
        )

        p1 = np.bitwise_or(np.left_shift(msb1, 16), lsw1)
        p2 = np.bitwise_or(np.left_shift(msb2, 16), lsw2)

        # alternate p1 and p2
        points = np.empty((2 * len(p1),), dtype=p1.dtype)
        points[0::2] = p1
        points[1::2] = p2

        # Two's complement
        points[points >= 0x7FFFFF] -= 0x1000000

        current = 5 / 0x7FFFFF * points / 500000
    else:
        most_sig = data[0::2]
        least_sig = data[1::2]

        d = np.left_shift(most_sig, 8) + least_sig
        r = np.double(np.uint16(np.int16(d + 0x8000)))
        f = r * 10 / 65536.0 - 5
        current = f * 2 / 1e6  # uA to A

    return current


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


if __name__ == "__main__":
    # test bytes2samples
    values = "ac ca 5c c5 a3 3a 53 35 ca ac c5 5c 3a a3 35 53 11 11 22 22 33 33 44 44 55 55 66 66 77 77 88 88"
    # values is a string of hex values
    data = np.array([int(x, 16) for x in values.split()])

    samples = bytes2samples(data)

    for i in range(0, len(samples)):
        print(f"Channel {i+1}: {samples[i]} A")
