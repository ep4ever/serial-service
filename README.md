## ep4ever Serial service

This is the command line backend python service that reads data comming
from serial RS485 connected epever series MPPT controller devices.
The data are saved in a json database file in the dbfiles folder on a daily basis.

## Getting started

You need to specify at least one device.
To do this you can use the command line interface like so:

```sh
python ./serialservice.py --device-name=6420an --device-port=/dev/ttyXRUSB0
```

> The service will not start if you provide those command line arguments

To start the service just use the same command with no argument.

```sh
python ./serialservice.py
```

To build the service use a git bash instead of the powershell console and run build.sh
command.

pypoetry is there only to provide a dependency management.
In order to use the pyinstaller packaging tool you must install the required package
listed in pyproject.toml with pip tool.
