import os
import flask

from pisite_app.common import ResponseData, jsonify_if_dataclass, StatusResponse, DataLine

import functools
import subprocess
import datetime
import json
import psutil
import libtmux
import mcstatus
import subprocess
import shlex
import threading

from flask_talisman import Talisman

# create and configure flaskapp
app = flask.Flask(__name__, instance_relative_config=True)

# load talisman defaults
Talisman(app)

# load the base config 
app.config.from_object("config")

# load deployment-specific config
app.config.from_pyfile("config.py")

if app.debug:
    print("debug mode, secret key: " + app.secret_key)

# server startup lock
lock = threading.Lock()

# run before each request
@app.before_request
def verify_connection():
    # print(flask.request.headers)
    # print(flask.request.data)
    # print(flask.request.remote_addr)
    if flask.request.remote_addr != app.config["PI_IP"]:
        return ResponseData(False, "IP address not accepted")
    try:
        client_api = flask.request.headers["Api-key"]
        if client_api != app.config["MAIN_API_KEY"]:
            return ResponseData(False, "invalid API key")
    except:
        return ResponseData(False, "missing API key")

# link all the routes

## API routes

@app.route("/api/ack", methods=("GET", ))
@jsonify_if_dataclass
def ack():
    return ResponseData(True, "pong! :)")

@app.route("/api/mc", methods=("GET","POST"))
@jsonify_if_dataclass
def minecraft():

    if flask.request.method == "GET":
        mc_status: MinecraftStatus = MinecraftStatus()
        return mc_status.to_response()
    if flask.request.method == "POST":
        try:
            data = json.loads(flask.request.data)
        except json.decoder.JSONDecodeError:
            return ResponseData(False, "invalid JSON")
        
        try:
            operation = data["operation"]
        except json.decoder.JSONDecodeError:
            return ResponseData(False, "must include operation field")
    
        result: dict = None
        if operation == "on":
            bad_response = None
            return_bad_response = False
            lock.acquire() # acquire lock
            try:
                mc_status: MinecraftStatus = MinecraftStatus()
                if mc_status.any_true:
                    return_bad_response = True
                    bad_response = ResponseData(False, "server is already on or starting up")
                else:
                    try:
                        result = start_minecraft()
                        return ResponseData(True)
                    except FileNotFoundError as e:
                        return_bad_response = True
                        bad_response = ResponseData(False, e.args[0])
            finally:
                lock.release() # release lock
            if return_bad_response:
                return bad_response
            if result == False:
                return ResponseData(False, "tmux error")
        elif operation == "off":
            # turn off minecraft server
            # TODO:
            return ResponseData(False, "unimplemented")
        else:
            return ResponseData(False, "invalid operation")

@app.route("/api/left", methods=("GET", "POST"))
@jsonify_if_dataclass
def left():
    if flask.request.method == "GET":
        return ResponseData(False, "unimplemented")
    if flask.request.method == "POST":
        return ResponseData(False, "unimplemented")

## dynmap

@app.route("/dynmap", methods=("GET",))
def page_dynmap():
    return flask.send_from_directory(app.config["DYNMAP_PATH"], "web/index.html")

# send anything inside the DYNMAP_PATH directory
@app.route("/dynmap/<path:ext>", methods=("GET",))
def dynmap_ext(ext):
    return flask.send_from_directory(app.config["DYNMAP_PATH"], ext)

## helper code

class MinecraftStatus():
    def __init__(self):
        self.tmux_window_running = False
        try:
            tmux_server = libtmux.Server()
            tmux_sessions = tmux_server.list_sessions()

            tmux_session_names = list()
            for session in tmux_sessions:
                # print(session.name)
                tmux_session_names.append(session.name)

            self.tmux_window_running = app.config["MC_TMUX_SESSION"] in [session.name for session in tmux_sessions]
        except:
            pass
        
        self.process_running = False
        try:
            for proc in psutil.process_iter():
                cmdline = proc.cmdline()
                # print(cmdline)
                for token in cmdline:
                    java = False
                    mc_or_forge = False
                    if "java" in cmdline:
                        java = True
                    if "forge" in token or "minecraft" in token:
                        mc_or_forge = True
                    if java and mc_or_forge:
                        self.process_running = True
        except:
            pass
        
        self.info = dict()
        self.mc_status_ping = False
        try:
            mc_server = mcstatus.MinecraftServer("localhost")
            ping = mc_server.ping()
            self.mc_status_ping = (ping > 0)

            query = mc_server.query()
            self.info["motd"] = query.motd
            self.info["players"] = query.players.names
        except:
            pass
    
        self.any_true = self.tmux_window_running or self.process_running or self.mc_status_ping

        # print("tmux: {}, proc: {}, mcquery: {}, any: {}".format(
        #     self.tmux_window_running,
        #     self.process_running,
        #     self.mc_status_ping,
        #     self.any_true)
        # )
    
    def to_response(self):
        statuses = {
            "mc_status_ping": self.mc_status_ping,
            "process_running": self.process_running,
            "tmux_window_running": self.tmux_window_running
        }

        return ResponseData(True, None, StatusResponse(any_power=self.any_true, statuses=statuses, info=self.info))
    
        
# preconditions: 
#   minecraft is not already running
#   lock is acquired
# throws FileNotFoundError
def start_minecraft():
    if not os.path.exists(app.config["MC_START_SCRIPT"]):
        raise FileNotFoundError("minecraft start script not found")
    if not os.path.isdir(app.config["MC_START_DIR"]):
        raise FileNotFoundError("minecraft start dir not found")

    try:
        tmux_server = libtmux.Server()
        # start the session
        _session = tmux_server.new_session(
            session_name=app.config["MC_TMUX_SESSION"], 
            start_directory=app.config["MC_START_DIR"], 
            window_command=app.config["MC_START_SCRIPT"],
        )
    except:
        return False
    
    return True