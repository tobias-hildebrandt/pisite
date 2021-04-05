import os

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import functools
import subprocess
import datetime
import json

from flask_talisman import Talisman
from flask_session import Session

try:
    import pisite_app.easy_executor as executor
except:
    import easy_executor as executor


# create and configure flaskapp
app = Flask(__name__, instance_relative_config=True)

# load talisman defaults
Talisman(app)

# load the base config 
app.config.from_object("config")

# load deployment-specific config
app.config.from_pyfile("config.py")

if app.debug:
    print("SECRET KEY IS: " + app.secret_key)

# load flask-session defaults
Session(app)


app.add_url_rule('/', endpoint='index')

# function decorator to require login
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        
        return view (**kwargs)
    return wrapped_view

# run before each request
@app.before_request
def load_logged_in_user():
    # load stuff into g, which can be used in templates
    g.user = session.get("username")

# link all the routes

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/controls", methods=("GET", "POST"))
@login_required
def controls():
    username = session["username"]
    if request.method == "POST":
        print("form data is {}".format(request.form))

        try:
            field_input = request.form["input_text"]
            script = request.form["command"]
        except KeyError:
            # user did not fill out some field
            flash("invalid input")
            return redirect(url_for("controls"))

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
            except executor.InvalidCommand:
                flash("invalid command!")

        return redirect(url_for("controls"))

    # else we are GET
    custom_text = datetime.datetime.now().ctime()

    scripts = executor.get_valid_scripts(username)
    
    return render_template("controls.html", scripts=scripts, customtext="Page loaded at: {}".format(custom_text))

@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        
        valid = False
        try:
            username = request.form["username"]
            password = request.form["password"]
            # contructor throws exeption on bad login
            success = executor.check_login(username, password)

            print("login success: {}".format(success))
            
            valid = success
        except Exception as e:
            valid = False
            print("caught exception on login POST: {}".format(e))

        if valid:
            session.clear()
            session["username"] = username
            session["password"] = password
            session.permanent = True
            flash("big success")
            return redirect(url_for("index"))
        else:
            # flask bad login
            flash("bad login")
    # else GET
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))
