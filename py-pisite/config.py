# general config, version controlled

import datetime

# use filesystem
SESSION_TYPE = "filesystem"
SESSION_FILE_DIR = "./instance/flask_session"
# security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
# lifetime
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)

# https://stackoverflow.com/a/43263483
JSON_SORT_KEYS = False