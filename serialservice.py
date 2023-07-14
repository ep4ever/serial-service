#!/usr/bin/env python
from dotenv import dotenv_values
import sys
import os
import json

from epforever.app import EpforEverApp

if __name__ == '__main__':
    # looking for main config location file
    config = None
    dconfig = dotenv_values(".env")
    lconfig = dconfig.get('MAIN_CONFIG_PATH')

    if not os.path.isfile(lconfig):
        print("API ERROR: main config.json could not be read")
        sys.exit(1)

    f = open(lconfig)
    config = json.load(f)
    f.close()

    app = EpforEverApp(config=config)
    app.run()
