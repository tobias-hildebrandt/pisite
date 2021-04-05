# https://docs.gunicorn.org/en/latest/index.html
# gunicorn -c /path/to/this/file

command = "" # change to gunicorn executable (in venv)
pythonpath = "" # change to project dir
chdir = "" # change to dir before starting
pidfile = "" # should be accessable by user
user = "" # user for worker processes
group = "" # group or gid for worker processes
worker_tmp_dir = "/tmp" 
proc_name = "" 
daemon = False # do not daemonize, let the OS's service controller do it (systemd, rc.d, runit, etc)
bind = ["0.0.0.0:5000"] # addresses to bind to
workers = 9 # number of worker processes, should be about (2*cores)+1

# if you want gunicorn to write its own logs
# errorlog = ""
# accesslog = "" 

# if you want gunicorn to use syslog
syslog = True
syslog_addr = "unix://dev/log"
