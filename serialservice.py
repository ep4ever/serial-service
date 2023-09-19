#!/usr/bin/env python
from dotenv import dotenv_values

from epforever.app import EpforEverApp
from epforever.mariadb_adapter import MariaDBAdapter
from epforever.sqlitedb_adapter import SqliteDBAdapter
from epforever.tinydb_adapter import TinyDBAdapter


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
    app.run()
