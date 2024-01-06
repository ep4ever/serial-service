#!/usr/bin/env python
import argparse
import logging
from dotenv import dotenv_values
from epforever.app import EpforEverApp
from epforever.mariadb_adapter import MariaDBAdapter
from epforever.sqlitedb_adapter import SqliteDBAdapter
from epforever.tinydb_adapter import TinyDBAdapter

parser: argparse.ArgumentParser = argparse.ArgumentParser(
    description="EP4Ever Serial service client",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    '-m',
    '--mode',
    type=str,
    default='measurement',
    help='Service run mode can be measurement (the default) or diary_backup'
)

args = parser.parse_args()
arguments = vars(args)

if __name__ == '__main__':
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # noqa E505
    console_handler.setFormatter(formatter)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console_handler)

    logging.debug("reading dotenv configuration file...")
    dconfig = dotenv_values(dotenv_path=".env")
    mode = dconfig.get('MODE', 'tiny')
    logging.debug(f"We are in {mode} mode! Creating adapter instance...")
    adapter = None

    if mode == 'tiny':
        adapter = TinyDBAdapter(dconfig)
    if mode == 'maria':
        adapter = MariaDBAdapter(dconfig)
    if mode == 'sqlite':
        adapter = SqliteDBAdapter(dconfig)

    if adapter is None:
        logging.error("ERROR: unknown adapter {}".format(adapter))
        exit(1)

    logging.debug(f"Creating EpforEverApp with adapter for {mode}!")
    app = EpforEverApp(adapter=adapter)

    if arguments.get('mode') == 'measurement':
        logging.debug("Calling run method of app")
        app.run()
    elif arguments.get('mode') == 'diary_backup':
        logging.debug("Calling diary_backup method of app")
        app.diary_backup()
