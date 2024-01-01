#!/usr/bin/env python
import argparse
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
    dconfig = dotenv_values(dotenv_path=".env")
    mode = dconfig.get('MODE', 'tiny')
    adapter = None

    if mode == 'tiny':
        adapter = TinyDBAdapter(dconfig)
    if mode == 'maria':
        adapter = MariaDBAdapter(dconfig)
    if mode == 'sqlite':
        adapter = SqliteDBAdapter(dconfig)

    if adapter is None:
        print("ERROR: unknown adapter {}".format(adapter))
        exit(1)

    app = EpforEverApp(adapter=adapter)

    if arguments.get('mode') == 'measurement':
        app.run()
    elif arguments.get('mode') == 'diary_backup':
        app.diary_backup()
