import click

from flask import current_app, g
from flask.cli import with_appcontext

def get_usersfile():
    if 'usersfile' not in g:
        g.usersfile = None # TODO: return file
    pass # return accounts object

def init_usersfile():
    pass # initialize the usersfile
    
def close_usersfile():
    usersfile = g.pop('usersfile', None)
    
    if usersfile is not None:
        usersfile.close()

@click.command('init-usersfile')
@with_appcontext
def init_usersfile_command():
    init_usersfile()
    click.echo('Initialized the accounts file')
    
def init_app(app):
    app.teardown_appcontext() # if we need to close it
    app.cli.add_command(init_usersfile)