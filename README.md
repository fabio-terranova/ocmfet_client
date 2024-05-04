# OCMFET client

Client application for the OCMFET acquisition system developed by Elbatech. The client is intended to be run on a PC and it is used to display the acquired data in real time, communicating with the server application ([ocmfet-server-zero](https://github.com/fabio-terranova/ocmfet-server-zero) or [ocmfet-server-feedback](https://github.com/fabio-terranova/ocmfet-server-feedback)) running on the Raspberry Pi.

## Index

- [OCMFET client](#ocmfet-client)
  - [Index](#index)
  - [Running the application](#running-the-application)
    - [Installing Python 3.11 and required packages](#installing-python-311-and-required-packages)
      - [Using `pipenv`](#using-pipenv)
      - [Using `pip`](#using-pip)
    - [Usage](#usage)

## Running the application

### Installing Python 3.11 and required packages

To install Python 3.11, on Ubuntu, execute the following commands in the terminal:

```sh
sudo apt update
sudo apt install python3.11
```

On Windows, download the installer from the [official website](https://www.python.org/downloads/).

The application requires the following python packages:

- [PyQt5](https://pypi.org/project/PyQt5/)
- [pyqtgraph](https://pypi.org/project/pyqtgraph/)
- [numpy](https://pypi.org/project/numpy/)
- [scipy](https://pypi.org/project/scipy/)
- [PyYAML](https://pypi.org/project/pyyaml/)

One can use `pipenv` or install the required packages manually via `pip`.

#### Using `pipenv`

To install the required packages using `pipenv`, on Ubuntu, execute the following commands in the terminal:

```sh
sudo apt install pipenv
pipenv install
```

On Windows, execute the following commands in the terminal:

```sh
pip install pipenv
pipenv install
```

Then the application can be run using the following command (`python3` can be replaced by `python` on Windows):

```sh
pipenv run python3 main.py
```

#### Using `pip`

To install the required packages using `pip` execute the following commands in the terminal:

```sh
pip install requirements.txt
```

Then the application can be run using the following command:

```sh
python3 main.py
```

### Usage

The main script can be used as follows:

```sh
python3 main.py [-c <config_file>] [-l|-o]
```

The optional argument `-c` can be used to specify the configuration file to be used by the client. If the argument is not provided, the default configuration file `default.yaml` will be used. The optional argument `-l` can be used to open the acquisition window. The optional argument `-o` can be used to open the data analysis window (to be implemented).
