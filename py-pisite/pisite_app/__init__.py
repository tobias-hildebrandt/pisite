
from os import environ 

mode = environ.get("PISITE_MODE")

if mode == "PI":
    import pisite_app.pisite as site
elif mode == "MAIN":
    import pisite_app.mainsite as site
else:
    raise RuntimeError("must set environment varaible PISITE_MODE")

app = site.app