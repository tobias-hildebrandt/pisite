import os

from flask import Flask


def create_app(test_config=None):
    # create and configure flaskapp
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="", #TODO
        USERSFILE=os.path.join(app.instance_path, 'usersfile.txt')
    )
        
    if test_config is None:
        # we are using a real config
        app.config.from_pyfile('config.py', silent=True)
    else:
        # we are passing in a test config
        app.config.from_mapping(test_config)
    
    # make sure instance folder exist
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # idk what to do here
        
    # link auth blueprint TODO
    
    # return app because we are a factory
    return app