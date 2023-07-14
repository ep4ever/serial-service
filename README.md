## ep4ever Serial service

This is the command line backend python service for the ep4ever solar station software.
It reads data comming from a serial RS485/Modbus connected epever series MPPT controller devices.
The data are then saved in a json database file in the dbfiles folder on a daily basis.

## Getting started

> /!\ Before you start, make sure you have installed the drivers to handle your device serial communication.
> There will soon be a wiki page talking about how to handle this.

You need to specify at least one device before starting the service.
To do this edit the devices section of the main config.json file (cf. main project solar-station):

** example: devices section of the main configuration file**
```json
"devices": [
    {
        "name": "6420an",
        "port": "/dev/ttyXRUSB1"
    },
    {
        "name": "3910bp",
        "port": "/dev/ttyXRUSB0"
    },
    {
        "name": "3210an",
        "port": "/dev/ttyXRUSB1"
    }
],
```

Then copy .env.dist to **.env** and update the path of the main configuration (config.json) path.
Once done use:

```sh
python ./serialservice.py
```

To build the service use a git bash instead of the powershell console and run build.sh
command.

pypoetry is there only to provide a dependency management.
In order to use the pyinstaller packaging tool you must install the required package
listed in pyproject.toml with pip tool.
