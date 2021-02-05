#!/bin/bash

source venv-pisite/bin/activate
cd experimentzone/
coverage run -m unittest discover
coverage html
sensible-browser "$PWD""/htmlcov/index.html"