#!/bin/sh

VENV="/home/tobias/programming/pisite/venv-pisite/"
WORKING_DIR="/home/tobias/programming/pisite/py-pisite/"
MODULE_NAME="pisite_app"
PORT="5000"
WORKERS=9 # should be about (2 * cores) + 1

cd "$WORKING_DIR"
"$VENV""/bin/gunicorn" "$MODULE_NAME"":app" --bind 0.0.0.0:"$PORT" -w "$WORKERS"