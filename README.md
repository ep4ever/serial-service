## ep4ever Serial service

This is the command line backend python service for the ep4ever solar station software.
It reads data comming from a serial RS485/Modbus connected epever series MPPT controller devices.
The data are then saved in a json database file in the dbfiles folder on a daily basis.

## Getting started

> /!\ Before you start, make sure you have installed the drivers to handle your device serial communication.
> There will soon be a wiki page talking about how to handle this.

You need to specify at least one device.
To do this you can use the command line interface like so:

```sh
python ./serialservice.py --device-name=6420an --device-port=/dev/ttyXRUSB0
```
(!) device name will be a key in the json database and you will need to added to the config.json::devices section
of the application configuration file. (ex: devices: ["6420an"] in solar-station config.json file)

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
