import os

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import functools
import subprocess
import datetime
import json

from flask_session import Session

try:
    import pisite.easy_executor as executor
except:
    import easy_executor

def create_app(test_config=None):
    # create and configure flaskapp
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="abc", # TODO: change this
        SESSION_TYPE = "redis"
    )

    Session(app)
    
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
    username = session["username"]
    if request.method == "POST":
        print("form data is {}".format(request.form))

        field_input = request.form["input_text"]

        script = request.form["command"]

        # button = request.form

        password = session["password"]

        # print("post_text {} of type {}".format(post_text, type(post_text)))
        # print("username: {} of type {}".format(username, type(username)))
        # print("password: {} of type {}".format(password, type(password)))

        # don't do anything on empty input
        if script != "":
            flash("you sent: {} {}".format(script, field_input))
            try:
                rc, out, err = executor.run_as(username, password, "{} {}".format(script, field_input))

                print("rc:{}\nout:{}\nerr{}".format(rc, out, err))
                
                flash("return code: {}".format(rc))
                flash("stdout:\n{}".format(out))
                flash("stderr:\n{}".format(err))
            except subprocess.TimeoutExpired:
                flash("error! timeout")
            except json.JSONDecodeError:
                flash("unable to decode validation table, contact the web administrator!")
            except OSError:
                flash("unable to access validation table, contact the web administrator!")
            except easy_executor.InvalidCommand:
                flash("invalid command!")

        return redirect(url_for("controls.controls"))

    # else we are GET
    custom_text = datetime.datetime.now()

    scripts = easy_executor.get_valid_scripts(username)
    
    return render_template("controls.html", scripts=scripts, customtext="custom variable element, timestamp {}".format(custom_text))

@auth_bp.route("login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        valid = False
        try:
            # contructor throws exeption on bad login
            results = executor.run_as(username, password, None)

            print("results: {}".format(results))
            
            valid = True
        except Exception as e:
            valid = False
            flash("caught exception on login POST: {}".format(e))

        if valid:
            session.clear()
            session["username"] = username
            session["password"] = password
            flash("big success")
            return redirect(url_for("index"))
        else:
            # flask bad login
            flash("bad login")
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
    g.user = session.get("username")

