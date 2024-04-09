# OCMFET client

Client application for both the ***zero*** and ***feedback*** versions of the acquisition system developed by Elbatech. The client is intended to be run on a PC and it is used to control the acquisition system and display the acquired data in real time, communicating with the server application ([ocmfet-server-zero](https://github.com/fabio-terranova/ocmfet-server-zero) or [ocmfet-server-feedback](https://github.com/fabio-terranova/ocmfet-server-feedback)) running on the Raspberry Pi.

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

The packages can be installed using `pip` from the requirements file:

### Linux

```sh
pip3 install -r requirements.txt
```

### Windows

```sh
pip install -r requirements.txt
```

## Usage

Depending on the version of the acquisition system, the client can be run with or without the `-zero` argument. The client can be run using the following command:

```sh
py client.py [-zero]
```
