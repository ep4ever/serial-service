#!/usr/bin/env python

##
# @mainpage EP4Ever Serial Service Client
#
# @section description_main Description
#
# This application starts the EP4Ever Serial service client with a given arg
# (measurement or diary_backup). The application sets up logging, reads
# environment variables from .env file and creates an appropriate adapter
# instance based on the MODE variable. Then it initializes EpforEverApp
# and runs it accordingly to the specified mode.
#
# @section notes_main Notes
# - Actually in beta stage.
#
# Copyright (c) 2024 www.ep4ever.com.  All rights reserved.
##

import argparse
import logging
from dotenv import dotenv_values
from app import EpforEverApp
from mariadb_adapter import MariaDBAdapter  # noqa: E501
from sqlitedb_adapter import SqliteDBAdapter  # noqa: E501
from tinydb_adapter import TinyDBAdapter  # noqa: E501


##
# Dictionary mapping log levels to their corresponding integer values.
##
log_levels = {
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
}

##
# Command line parser.
##
parser = argparse.ArgumentParser(
    description="EP4Ever Serial service client",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

##
# Parse command line arguments for the script.
##
parser.add_argument(
    '-m',
    '--mode',
    type=str,
    default='measurement',
    help='Service run mode can be measurement (the default) or diary_backup'
)
##
# Gets the application console arguments
##
args = parser.parse_args()

##
# Get a dict of these arguments
##
arguments = vars(args)

##
# Create a StreamHandler to print log messages to stdout.
##
console_handler = logging.StreamHandler()

##
# Configure the handler with the desired logging level and formatter.
##
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

# reading dotenv configuration file
dconfig = dotenv_values(dotenv_path='.env')

##
# Get the log level from environment variable or fallback to DEBUG level.
##
loglevel = dconfig.get('LOG_LEVEL', log_levels.get('DEBUG'))

##
# Set up the root logger with the given log level and add the handler.
##
logging.getLogger().setLevel(log_levels.get(loglevel))
logging.getLogger().addHandler(console_handler)
logging.info(f"Log level setted to {loglevel}. Starting up...")

##
# Get the mode from environment variable or fallback to 'tiny' value.
##
mode = dconfig.get('MODE', 'tiny')

##
# Create an appropriate adapter instance based on the given mode.
##
logging.debug(f"We are in {mode} mode! Creating adapter instance...")
adapter = None
if mode == 'tiny':
    adapter = TinyDBAdapter(dconfig)
elif mode == 'maria':
    adapter = MariaDBAdapter(dconfig)
elif mode == 'sqlite':
    adapter = SqliteDBAdapter(dconfig)
if adapter is None:
    logging.error(f"ERROR: unknown adapter {adapter}")
    exit(1)

##
# Initialize EpforEverApp instance with the given adapter.
##
logging.debug(f"Adapter for {mode} is initialized! creating App")

##
# The EpforEver application instance created with the
# selected adapter setted in dotenv file
##
app = EpforEverApp(adapter=adapter)

if arguments.get('mode') == 'measurement':
    logging.info(
        f"Starting ep4ever serialservice application in {mode} mode"
    )
    app.run()
elif arguments.get('mode') == 'diary_backup':
    logging.info(
        'Starting ep4ever serialservice application in diary backup mode'
    )
    app.diary_backup()
