# OCMFET client

Client application for the OCMFET acquisition system developed by Elbatech. The client is intended to be run on a PC and it is used to display the acquired data in real time, communicating with the server application ([ocmfet-server-zero](https://github.com/fabio-terranova/ocmfet-server-zero) or [ocmfet-server-feedback](https://github.com/fabio-terranova/ocmfet-server-feedback)) running on the Raspberry Pi.

## Index

- [OCMFET client](#ocmfet-client)
  - [Index](#index)
  - [Requirements](#requirements)
    - [Linux](#linux)
    - [Windows](#windows)
  - [Usage](#usage)

## Requirements

The client application is written in Python 3 and it requires the following packages:

- [PyQt5](https://pypi.org/project/PyQt5/)
- [pyqtgraph](https://pypi.org/project/pyqtgraph/)
- [numpy](https://pypi.org/project/numpy/)
- [scipy](https://pypi.org/project/scipy/)
- [PyYAML](https://pypi.org/project/pyyaml/)

All the required packages can be installed using `pip` by running the following command in the terminal:

### Linux

```sh
pip3 install -r requirements.txt
```

### Windows

```sh
pip install -r requirements.txt
```

## Usage

The client application can be run by executing the following command in the terminal:

```sh
py client.py [-c <config_file>] [-l|-o]
```

The optional argument `-c` can be used to specify the configuration file to be used by the client. If the argument is not provided, the default configuration file `default.yaml` will be used. The optional argument `-l` can be used to start the acquisition window immediately after the client is started. The optional argument `-o` can be used to start the offline analysis window immediately after the client is started.
