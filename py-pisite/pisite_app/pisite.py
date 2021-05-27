import os

import flask
from pisite_app.common import ResponseData, load_data, print_session_cookies
import pisite_app.auth as auth

import functools
import subprocess
import datetime
import json
import requests
import subprocess
import shlex
import wakeonlan

from flask_talisman import Talisman
from flask_session import Session

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

# load flask-session defaults
Session(app)

# set up sqlalchemy inside auth
auth.db.init_app(app)

app.add_url_rule('/', endpoint='index')

# set up http client with certificates
request_session: requests.Session = requests.Session()
request_timeout = 1 # seconds
request_session.verify = app.config["PATH_TO_MAIN_CERTFILE"]

# function decorator to require login
def require_login(func):
    @functools.wraps(func)
    def wrapped_func(**kwargs):
        if flask.session.get("user_id") is None:
            # session["username"] = None
            return ResponseData(False, "login required")()
        
        return func (**kwargs)
    return wrapped_func

# function decorator to require group membership
def require_group(group):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(**kwargs):
            user = current_user()
            desired_group = auth.Group.query.filter(auth.Group.name == group).first()

            if desired_group is None or desired_group not in user.groups:
                return ResponseData(False, "insufficient group membership")()

            return func (**kwargs)
        return wrapped_func
    return decorator

# function decorator to require login
def page_require_login(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if flask.session.get("user_id") is None:
            return flask.redirect(flask.url_for('page_login'))
        
        return view (**kwargs)
    return wrapped_view

# run before each request
@app.before_request
def before():
    user = current_user()
    
    # load stuff into g, which can be used in templates
    flask.g.username = None if user is None else user.username

    print("request from user: {}".format(str(user)))

    # debug cookies
    # print_session_cookies()

    # print request headers
    # print("headers:")
    # for header in flask.request.headers:
    #     print(header)


# link all the routes

## HTML+JS page routes
@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/controls", methods=("GET",))
@page_require_login
def page_controls():
    return flask.render_template("controls.html")

@app.route("/login", methods=("GET",))
def page_login():
    return flask.render_template("login.html")

#TODO: put these on mainsite and forward requests
# @app.route("/dynmap", methods=("GET",))
# @page_require_login
# def page_dynmap():
#     return flask.send_file("dynmap/web/index.html")

# @app.route("/dynmap/<path:ext>", methods=("GET",))
# @require_login
# def dynmap_ext(ext):
#     filepath = "pisite_app/dynmap/{}".format(ext)
#     # print("current dir: {}".format(os.path.abspath(os.curdir)))
#     # print("filepath: {}".format(filepath))
#     if os.path.exists(filepath):
#         return flask.send_file("dynmap/{}".format(ext))
#     else:
#         return flask.abort(404)

# API routes

@app.route("/api/login", methods=("POST",))
def api_login():
    try:
        data = json.loads(flask.request.data)
    except json.decoder.JSONDecodeError:
        return ResponseData(False, "invalid JSON")()

    # clear current user if any
    flask.session["user_id"] = None

    fail_data = {
        "current_user": None
    }

    valid = False
    try:
        username = data["username"]
        password = data["password"]
    except (json.decoder.JSONDecodeError, KeyError):
        valid = False
        return ResponseData(False, "must include fields username and password", fail_data)()
    
    # validate login here
    if username is None or username == "" or password is None or password is "":
        valid = False
    else:
        valid, user = auth.validate_user(username, password)
    
    print("valid login? {} {}: {}".format(username, password, valid)) #TODO: remove
    
    if valid:
        # set session user_id
        flask.session["user_id"] = user.id
        flask.session.permanent = True
        return ResponseData(True, None, {
            "current_user": username
        })()
    else:
        return ResponseData(False, "invalid login details", fail_data)()

@app.route("/api/logout", methods=("POST",))
def api_logout():
    # TODO: invalidate session
    flask.session["user_id"] = None
    return ResponseData(True, None, {
        "current_user": None
    })()

# TODO: remove this?
@app.route("/api/controls", methods=("GET",))
@require_login
def api_controls():
    # TODO: get information from main
    return ResponseData(True, None, {
        "controls": [
            ("minecraft", "/api/main/mc"),
            ("left 4 dead 2", "/api/main/l4d2"),
        ]
    })()

@app.route("/api/account", methods=("GET", "POST"))
@require_login
def api_account():
    user = current_user()
    if flask.request.method == "GET":
        return ResponseData(True, None, {
            "username": user.username
        })()

    if flask.request.method == "POST":
        try:
            data = json.loads(flask.request.data)
        except json.decoder.JSONDecodeError:
            return ResponseData(False, "invalid JSON")()
        try:
            new_password = data["new_password"]
        except (json.JSONDecodeError, KeyError):
            return ResponseData(False, "must include field new_password")()

        success, message = auth.change_password(user, new_password)

        if not success:
            return ResponseData(False, message)()
        else:
            return ResponseData(True)()
        

@app.route("/api/admin", methods=("GET", "POST"))
@require_login
@require_group("admin")
def api_admin():
    # user = current_user()
    # admin_group = auth.Group.query.filter(auth.Group.name == "admin").first()

    # if admin_group is None or admin_group not in user.groups:
    #     return ResponseData(False, "insufficient group membership")()

    if flask.request.method == "GET":
        users = [user.to_detail_dict() for user in auth.get_users()]
        groups = [group.to_detail_dict() for group in auth.get_groups()]
        reg_keys = [reg_key.to_detail_dict() for reg_key in auth.get_reg_keys()]
        
        return ResponseData(True, None, {
            "users": users,
            "groups": groups,
            "reg_keys": reg_keys
        })()

    if flask.request.method == "POST":
        try:
            data = json.loads(flask.request.data)
        except json.decoder.JSONDecodeError:
            return ResponseData(False, "invalid JSON")()

        try:
            operation = data["operation"]
            target = data["target"]
        except KeyError:
            return ResponseData(False, "must include fields operation and target")()
        
        if operation == "delete_user":
            success = auth.remove_user(target)
            return ResponseData(success)()
        if operation == "delete_reg_key":
            success = auth.remove_reg_key(target)
            return ResponseData(success)()

@app.route("/api/power", methods=("POST", "GET"))
@require_login
def power():
    if flask.request.method == "GET":
        command = shlex.split("ping -c 1 -W 1 {}".format(app.config["MAIN_IP"]))
        pingable = subprocess.run(command).returncode == 0 # returncode 0 is success

        connectable = False
        response: flask.Response = forward_to_main("/api/ack")
        if json.loads(response.data)["success"]:
            connectable = True

        return ResponseData(True, None, {
            "is_main_pingable": pingable,
            "is_main_connectable": connectable
        })()
    if flask.request.method == "POST":
        # send the WoL packet
        try:
            wakeonlan.send_magic_packet(app.config["MAIN_MAC"])
        except ValueError:
            return ResponseData(False, "invalid MAC address")()
        return ResponseData(True)()


#TODO: remove 
@app.route("/api/test", methods=("POST",))
def test():
    # this is just a test

    try:
        data = json.loads(flask.request.data)
    except json.decoder.JSONDecodeError:
        return ResponseData(False, "invalid JSON")()
    try:
        test = data["test"]
    except:
        return ResponseData(False, "must include field test")()

    return ResponseData(True, "test message", {
        "your_test": test,
        "qwerty": "uiop"
    })()

## forwarded routes to main

# main api endpoints
@app.route("/api/main/<endpoint>", methods=("GET", "POST"))
@require_login
def forward_api_to_main(endpoint):
    return forward_to_main("api/{}".format(endpoint))

# dynmap
@app.route("/dynmap", methods=("GET",))
@page_require_login
def page_dynmap():
    return forward_to_main("dynmap")

@app.route("/dynmap/<path:ext>", methods=("GET",))
@require_login
def dynmap_ext(ext):
    return forward_to_main("dynmap/{}".format(ext))

## helper code

def forward_to_main(main_endpoint) -> flask.Response:
    main_url = "https://{}:{}/{}".format(
        app.config["MAIN_IP"],
        app.config["MAIN_PORT"],
        main_endpoint
    )
    new_headers = {}
    for (key, val) in flask.request.headers:
        new_headers[key] = val
    new_headers["Api-key"] = app.config["PI_API_KEY"]
    try:
        main_response: requests.Response = request_session.request(
            method=flask.request.method,
            url=main_url,
            headers=new_headers,
            data=flask.request.data,
            timeout=request_timeout
        )

        response: flask.Response = flask.make_response()
        response.status = str(main_response.status_code)
        for (key, val) in main_response.headers.items():
            response.headers[key] = val
        response.data = main_response.content
        
        return response
    except requests.exceptions.ReadTimeout:
        return ResponseData(False, "connection to main timed out")()
    except requests.exceptions.ConnectionError:
        return ResponseData(False, "unable to connect to main")()
    except json.decoder.JSONDecodeError:
        return ResponseData(False, "invalid JSON response from main")()

def current_user() -> auth.User:
    user_id = flask.session.get("user_id")
    if user_id is None:
        return None
    else:
        return auth.get_user(user_id)