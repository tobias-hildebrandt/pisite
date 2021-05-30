import os

import flask
from pisite_app.common import ResponseData, print_session_values, print_request_headers
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

# function decorator to require JSON depending on request http method
# only works for flat json objects
# also load request data into flask.g.request_data
def require_json_fields(post: list=None, get: list=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(**kwargs):
        
            if flask.request.method == "POST":
                target_list = post
            elif flask.request.method == "GET":
                target_list = get

            if target_list is not None and len(target_list) != 0:
                result = verify_json_field_names(*target_list)
                if result is not None:
                    return result
                flask.g.request_data = json.loads(flask.request.data)
            
            # if reached here, all is good
            return func (**kwargs)
        return wrapped_func
    return decorator
    

# run before each request
@app.before_request
def before():
    user = current_user()
    
    # load stuff into g, which can be used in templates
    flask.g.username = None if user is None else user.username

    print("request from user: {}".format(str(user)))

    # debug prints
    if app.debug:
        # print_session_values()
        print_request_headers()


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

# API routes

# attempt to login user, will log out user before attempting
@app.route("/api/login", methods=("POST",))
@require_json_fields(post=["username", "password"])
def api_login():

    # clear current user if any
    flask.session["user_id"] = None

    username = flask.g.request_data["username"]
    password = flask.g.request_data["password"]

    # attempt to validate user here
    valid, user = auth.validate_user(username, password)
    
    # TODO: remove this to not leak password attempts in terminal
    if app.debug:
        print("valid login? {} {}: {}".format(username, password, valid))
    
    if valid:
        # set session user_id
        flask.session["user_id"] = user.id
        flask.session.permanent = True
        return ResponseData(True, None, {
            "current_user": username
        })()
    else:
        # on fail, tell user that it is logged out
        return ResponseData(False, "invalid login details", {
            "current_user": None
        })()

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
@require_json_fields(post=["new_password"])
@require_login
def api_account():
    user = current_user()
    if flask.request.method == "GET":
        return ResponseData(True, None, {
            "username": user.username
        })()

    if flask.request.method == "POST":
        new_password = flask.g.request_data["new_password"]

        success, message = auth.change_password(user, new_password)

        if not success:
            return ResponseData(False, message)()
        else:
            # TODO: log out all other sessions for current user
            return ResponseData(True)()
        

@app.route("/api/admin", methods=("GET", "POST"))
@require_json_fields(post=["operation", "target"])
@require_login
@require_group("admin")
def api_admin():

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
        operation = flask.g.request_data["operation"]
        target = flask.g.request_data["target"]
        
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
        # try to ping it
        command = shlex.split("ping -c 1 -W 1 {}".format(app.config["MAIN_IP"]))
        pingable = subprocess.run(command).returncode == 0 # returncode 0 is success

        # try to send a request to main
        connectable = False
        response: flask.Response = forward_to_main("/api/ack")
        if json.loads(response.data)["success"]:
            connectable = True

        # return the results
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
@app.route("/api/test", methods=("POST", "GET"))
@require_json_fields(post=["test"])
def test():
    # this is just a test
    if flask.request.method == "GET":
        return ResponseData(True, "test message", {
            "this_was_a_get": True
        })()
    if flask.request.method == "POST":
        return ResponseData(True, "test message", {
            "your_test": flask.g.request_data["test"],
            "foo": "bar"
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

# return None for success
def verify_json_field_names(*field_names):
    # attempt to simply load json into a dict
    try:
        data = json.loads(flask.request.data)
    except json.decoder.JSONDecodeError:
        return ResponseData(False, "invalid JSON")()
    
    # verify that the json has the right fields
    for field in field_names:
        try:
            data[field]
        except KeyError:
            return ResponseData(False, "missing some required fields", {
                "required_fields": field_names
            })()
    
    return None