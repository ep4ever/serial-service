#!/usr/bin/env python
from dotenv import dotenv_values
# import sys
from epforever.app import EpforEverApp
from epforever.tinydb_adapter import TinyDBAdapter
from epforever.mariadb_adapter import MariaDBAdapter
from epforever.sqlitedb_adapter import SqliteDBAdapter


if __name__ == '__main__':
    dconfig = dotenv_values(".env")
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
    app.run()
