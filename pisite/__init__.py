import os

from flask import Flask

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import functools
import subprocess
import datetime
import jsonpickle

try:
    import pisite.repl_connection as repl_connection
except:
    import repl_connection

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
    def hello(): # pylint: disable=unused-variable
        return """Hello, World! <a href="index">index</a>"""

    @app.route("/")
    def index(): # pylint: disable=unused-variable
        return render_template("index.html")

    app.add_url_rule('/', endpoint='index')

    app.register_blueprint(auth_bp)

    app.register_blueprint(controls_bp)
    
    # return app because we are a factory
    return app

command_name = "repl_shell.py"
dir_path = os.path.dirname(os.path.realpath(__file__))
command = "'python {}'".format(os.path.join(dir_path, command_name))

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

        repl_conn = jsonpickle.decode(session["repl_conn"])

        print(repl_conn)

        results_dict = repl_conn.give_repl_exec_command(post_text)
        
        flash("you sent: {}".format(post_text))
        flash("output:\n{}".format(results_dict))
        return redirect(url_for("controls.controls"))

    # else
    custom_text = datetime.datetime.now()
    return render_template("controls.html", customtext="custom variable element, timestamp {}".format(custom_text))

@auth_bp.route("login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        valid = False
        try:
            # contructor throws exeption on bad login
            repl_conn = repl_connection.REPLConnection(command, username, password)
            print(repl_conn)
            
            valid = True
        except Exception as e:
            valid = False
            flash("exception: {}".format(e))

        if valid:
            session.clear()
            session["user"] = username
            session["repl_conn"] = jsonpickle.encode(repl_conn)
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

