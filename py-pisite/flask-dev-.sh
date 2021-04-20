#!/bin/bash

VENV="/home/tobias/programming/pisite/venv-pisite/"
WORKING_DIR="/home/tobias/programming/pisite/py-pisite/"
MODULE_NAME="pisite_app"

. "$VENV"/bin/activate

cd "$WORKING_DIR"

FLASK_ENV=development FLASK_APP="$MODULE_NAME" flask run "$@"
