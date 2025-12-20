# OCMFET client

Client application for the OCMFET acquisition system developed by Elbatech. The client is intended
to be run on a PC and it is used to display the acquired data in real time, communicating with the
server application ([ocmfet-server-zero](https://github.com/fabio-terranova/ocmfet-server-zero) or
[ocmfet-server-feedback](https://github.com/fabio-terranova/ocmfet-server-feedback)) running on the
Raspberry Pi.

## Screenshot

<img width="2073" height="1177" alt="image" src="https://github.com/user-attachments/assets/8cdc7c9f-91f6-43e1-bb64-0ab82492610f" />

## Installation

### Prerequisites

To install Python 3.11 and the GitHub CLI, on Ubuntu, execute the following commands in the terminal:

```sh
sudo apt update
sudo apt install python3.11 gh
```

On Windows, download the installers from the [official website](https://www.python.org/downloads/) and
the [official website](https://cli.github.com/).

### Installing the package

To install the package, clone the repository and install the package using pip:

```sh
gh repo clone fabio-terranova/ocmfet_client
cd ocmfet_client
git submodule update --init --recursive
pip install .
```

### Usage

To run the client, execute the following command in the terminal:

```sh
ocmfet_client [-c <config_file>] [-l | -o]
```

The optional argument `-c` can be used to specify the configuration file to be used by the client.
If the argument is not provided, a default configuration file (`default.yaml`) will be used. The
optional argument `-l` can be used to open the acquisition window. The optional argument `-o` can be
used to open the data analysis window (to be implemented).

## Development

Using [Hatch](https://hatch.pypa.io/latest/#hatch) and [pre-commit](https://pre-commit.com/) for
development.

### Install Hatch

To install Hatch, on Ubuntu, execute the following command in the terminal:

```bash
pip install hatch
```

On Windows, follow the instructions on the
[official website](https://hatch.pypa.io/latest/#installation).
