#!/usr/bin/env python
import yaml
import argparse
import sys

from epforever.app import EpforEverApp


def argumentParser(config: dict):
    devices = config.get('devices') or []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--device-name',
        help='new device name'
    )
    parser.add_argument(
        '--device-port',
        help='new device port'
    )
    args = parser.parse_args()
    if (
            args.device_name is not None and args.device_port is None or
            args.device_port is not None and args.device_name is None):
        parser.print_help()
        sys.exit(1)

    if args.device_name is not None and args.device_port is not None:
        for device in devices:
            if device.get('name') == args.device_name:
                print("Warning: {} already exists".format(args.device_name))
                sys.exit(1)
            if device.get('port') == args.device_port:
                print("Warning: {} already exists".format(args.device_port))
                sys.exit(1)

        devices.append({
            'name': args.device_name,
            'port': args.device_port
        })

        config['devices'] = devices
        content = yaml.dump(config)
        with open('config.yaml', 'w') as f:
            f.write(content)

        """
        if using the command line argument we do not start
        the service in order to be able to add more than one device.
        """
        sys.exit(0)

    if len(devices) == 0:
        print("Warning no devices defined!")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    config = None

    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Could not find config.yaml file")
        sys.exit(1)

    argumentParser(config=config)

    app = EpforEverApp(config=config)
    app.run()
