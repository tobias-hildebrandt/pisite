import os

from flask import Flask

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import functools
import subprocess
import datetime

import pisite.basic_auth as basic_auth

def create_app(test_config=None):
    # create and configure flaskapp
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev change me", # TODO: change this
    )
        
    if test_config is None:
        # we are using a real config
        app.config.from_pyfile("config.py", silent=True)
    else:
        # we are passing in a test config
        app.config.from_mapping(test_config)
    
    # make sure instance folder exist
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # idk what to do here
        
    # TODO: link stuff

    @app.route("/hello")
    def hello():
        return """Hello, World! <a href="index">index</a>"""

    @app.route("/")
    def index():
        return render_template("index.html")

    app.add_url_rule('/', endpoint='index')

    app.register_blueprint(auth_bp)

    app.register_blueprint(controls_bp)
    
    # return app because we are a factory
    return app

auth = basic_auth.BasicAuth()
auth.create_user("test", "test", force_password=True)

auth_bp = Blueprint("auth", __name__, url_prefix="/")

controls_bp = Blueprint("controls", __name__, url_prefix="/")

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view (**kwargs)
    return wrapped_view

@controls_bp.route("controls", methods=("GET", "POST"))
@login_required
def controls():
    if request.method == "POST":
        post_text = request.form["input_text"]
        flash_text=""
        if post_text == "uname":
            flash_text = subprocess.run("uname -a".split(" "), stdout=subprocess.PIPE).stdout
        elif post_text == "ls":
            flash_text = subprocess.run("ls -l".split(" "), stdout=subprocess.PIPE).stdout
        elif post_text == "pwd":
            flash_text = subprocess.run("pwd", stdout=subprocess.PIPE).stdout
        elif post_text == "custom":
            flash_text = subprocess.run("pisite/custom.sh", stdout=subprocess.PIPE, shell=True).stdout
        else:
            flash_text = b"looks like you didn't put in a registered command"

        flash("you sent: {}".format(request.form["input_text"]))
        flash("output:\n{}".format(flash_text.decode()))
        return redirect(url_for("controls.controls"))

    # else
    custom_text = datetime.datetime.now()
    return render_template("controls.html", customtext="custom variable element, timestamp {}".format(custom_text))

@auth_bp.route("login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            valid = auth.validate_user(username, password)
        except basic_auth.UserExistenceException:
            valid = False

        if not valid:
            flash("wrong login details")
        else:
            session.clear()
            session["user"] = username
            flash("big success")
        return redirect(url_for("controls.controls"))

    # else GET
    return render_template("login.html")

@auth_bp.route("logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route("success")
@login_required
def success():
    return '''BIG NUTT <a href="/">home</a>'''

@auth_bp.before_app_request
def load_logged_in_user():
    g.user = session.get("user")

