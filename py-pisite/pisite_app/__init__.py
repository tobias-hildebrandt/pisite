
from os import environ 

mode = environ.get("PISITE_MODE")

global app

if mode == "PI":
    import pisite_app.pisite as site
    app = site.app
elif mode == "MAIN":
    import pisite_app.mainsite as site
    app = site.app
else:
    print("NOTICE: no PISITE_MODE envinronment set!!")