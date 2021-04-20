#!/bin/sh

export PISITE_MODE="MAIN" 
export FLASK_RUN_PORT="5001"
export FLASK_RUN_CERT="./instance/maincert.pem"
export FLASK_RUN_KEY="./instance/mainkey.pem"
./flask-dev-.sh 
