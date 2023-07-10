#!/usr/bin/python

import json
import os
import sys
from pathlib import Path

from epforever.app import EpforEverApp


def start():
    lconfig = os.path.join(
        Path(__file__).resolve().parent.parent.parent,
        'config.json'
    )
    if not os.path.isfile(lconfig):
        if not os.path.isfile('config.json'):
            print("ERROR: missing configuration file config.json")
            sys.exit(1)
        else:
            # in production file conf is within the same path
            lconfig = 'config.json'

    f = open(lconfig)
    config = json.load(f)
    f.close()

    app = EpforEverApp(config=config)
    app.run()
