# general config, version controlled

import datetime

# use redis
SESSION_TYPE = "redis"
# security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
# lifetime
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)