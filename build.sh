#!/bin/sh

pyinstaller --paths=$PWD --distpath=$PWD/dist --onefile serialservice.py
rm -rf build
rm serialservice.spec
