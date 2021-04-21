
# depedencies:
see required_packges.txt

# links
https://flask.palletsprojects.com/en/1.1.x/
https://flask-login.readthedocs.io/en/latest/
https://passlib.readthedocs.io/en/stable/index.html
https://flask-session.readthedocs.io/en/latest/

# password storage
encrypt passwords with passlib/bcrypt
use a dictionary to store them
write to text file 

# TODO:
add actual account system (look back in git and re-use code?)
add auto-refresh status divs during boot up
test deployment on real hardware
add autoshutdown for games and hardware
rewrite html+js frontend in some more organized framework

# notes on flask
https://overiq.com/flask-101/sessions-in-flask/
session is like a dict that is stored and read in order to process a request
session data is stored by default in a cookie sent to the client
client-side sessions should NOT hold sensitive information, they are only signed, not encrypted
the instance folder is only used with custom server-side instances, such as Flask-Session
https://stackoverflow.com/questions/19760486/resetting-the-expiration-time-for-a-cookie-in-flask

# client -> server communication
send raw username+password over HTTPS
https://flask.palletsprojects.com/en/1.1.x/security/

# ajax methods
two ajax applications, one on the pi and one on the main server
RESTful API on endpoint /api/*
html+js on /{index,login,controls,etc...}
main server connection is only open to the pi (via IP check and API key check)
pi:
    login (via session cookies)
    serves JS+HTML application
    add buttons specific to each user, maybe?
    buttons may include:
        turn on main server
        start minecraft server
    ajax needs short timeout in case main server is off
main server:
    HTTP api only (no graphical interface)
    needs api endpoints for each game control
    set up some kind of auto-shutdown? (maybe separate from the api program)
    add some kind of mutex lock for executing shell programs or use work queue?

RESTful API on pi (
    all require valid cookie except /api/login,
    maybe attempt to deny http clients that say they are a web browser?
):
/api/login:
    POST will log in and return a session cookie
/api/logout:
    POST will invalidate session cookie
/api/controls:
    GET will return all available controls to the cookie, maybe??
/api/power:
    GET will return status of the server (via ping)
    POST will send out wake-on-lan magic packet
/api/main/*
    will forward request to mainserver and send back response

RESTful API on mainserver (all require pi's certificate in request):
/api/*:
    GET will return status of a game server
    POST will perform an operation on the server, e.g. {"operation": "on"}

# alternatives to javascript
make sure it complies with libreJS and has permissible license?
typescript or coffescript
dart
gwt - google web toolkit (java)
elm or purescript or clojurescript (functional)
webassembly (c/c++/rust/many more, interact with DOM through JS)
- (maybe use SDL with webassembly?)
- https://github.com/shlomnissan/sdl-wasm 
- https://subscription.packtpub.com/book/game_development/9781838644659/1
haxe
any language that can transpile to JS:
https://github.com/jashkenas/coffeescript/wiki/List-of-languages-that-compile-to-JS

# dynmap
install dynmap to minecraft server (put the jar in /mods)
start minecraft server to generate files
stop server

move `$(mc install location)/dynmap/map` to `DYNMAP_PATH` (instance `config.py`)
`dynmap/web/` should have:
    css/
    images/
    js/
    index.html
    etc...
to every href or src tag in `index.html`, insert `dynmap/web/` (config.js should be in standalone, see below to generate it)
edit (only) absolute paths in files found in `grep -r . -e "images/"` and `grep -r . -e "js/"`
add `dynmap/web/`
thus, `js/map.js`, `js/hdmap.js`, `js/playermarkers.js`, NOT! `css/leaflet.css`, `css/dynmap_style.css`
`link.png` in `css/dynmap_style.css` needs to be absolute
edit configuration.txt in `$(mc install location)/dynmap/configuration.txt`
<!-- to generate `standalone/config.js`, `disable-webserver` should be false, even with `class: org.dynmap.JsonFileClientUpdateComponent` active
start the server, it should generate the `standalone/config.js`
then, `disable-webserver` can be set to true (be sure the edit the paths!!)
alternatively, copy-paste this into `standalone/config.js`:-->
```js
var config = {
    url : {
        configuration: 'dynmap/web/standalone/dynmap_config.json?_={timestamp}',
        update: 'dynmap/web/standalone/dynmap_{world}.json?_={timestamp}',
        sendmessage: 'dynmap/web/standalone/sendmessage.php',
        login: 'dynmap/web/standalone/login.php',
        register: 'dynmap/web/standalone/register.php',
        tiles: 'dynmap/web/tiles/',
        markers: 'dynmap/web/tiles/'
    }
};
```
actually, it looks like `standalone/config.js` is generated on the fly somehow
so we will just change where the html/js looks for it in `index.html`
change the line from `standalone/config.js` to `custom_config.js` and copy-paste above js lines into `custom_config.js`
also, move the js code out of `index.html` and into `custom_config.js`

to change what part of the world is rendered, edit `$(mc install location)/dynmap/worlds.txt`
the indentation is funky, but set text editor to yaml with tab spacing of 2

~~to disable clock, comment out all of timeofdayclock.js~~
to disable clock, comment out lines in `$(mc install location)/dynmap/configuration.txt` concerning "clock"