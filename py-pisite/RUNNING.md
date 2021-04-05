# run the webserver

create a python venv at some location accessable by the unix user destined to run the webserver
`python -m venv path_to_venv`

activate venv
`. path_to_venv/bin/activate`

install required dependencies
`pip install -r required-packages.txt`

edit shell script
`vi run-in-shell.sh`

run it
`./run-in-shell.sh`

# using a systemd service