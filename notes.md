
# depedencies:
flask
passlib
bcrypt

# links
https://flask.palletsprojects.com/en/1.1.x/
https://flask-login.readthedocs.io/en/latest/
https://passlib.readthedocs.io/en/stable/index.html

# password storage
encrypt passwords with passlib/bcrypt
use a dictionary to store them
write to text file 

# TODO:
add group permissions to basic_auth
add validation after yaml read
change project directory structure
see if flask-login is necessary

# client -> server communication
send raw username+password over HTTPS

# permissions brainstorming
idea 1 (current):
- data store contains application-specific usernames+passwords
- "groups" and "permissions" in data store define which commands a user can run
- the web server calls a subprocess to run a command
- possible to use doas/sudo to allow subprocess to change unix users, instead of command running as the web server's unix user
- must configure doas/sudo to allow the web server's unix user permission to execute certain commands as each user

idea 2:
- data store contains application-specific usernames+passwords
- contains ssh private key instead of "group" or "permissions"
- each machine to which the user needs access (including local machine?) must have a unix account set up that accepts the key
- administration & permission control is done via unix 
- on web page button press, web server would use an ssh client to connect to a machine to run a command as that remote unix user
- could still limit access via web server (?) only accept certain command in POSTs

idea 3:
- no data store
- user would use unix username and password-part to "log in" 
- keep some kind of logged-in process active during session (chrooted? REPL? unset $PROMPT?)
- set unix password to some string mixed with a secret stored by the server
- thus, users cannot log in via standalone ssh, only through the web server
- to run command, web server uses subprocess (REPL? which creates its own workers) which is run *as* the unix user via doas/sudo/su (no setup needed)
- use shared data structure / unix sockets / unix named pipes
- administration & permission control is done via unix

idea 4 (?):
- the webserver serves a webpage with a js ssh client with some preset buttons that do something in the ssh client
- single page application? entirely front end, no async with web server
- dead simple web server (just serve the SPA and let ssh do the work lmao)
- all permissions, auth, administration would be done via unix & ssh

idea 5:
- same as 1, but have a separate process with sudo permissions read from a work queue or something
- isolates permission escalation attack vector to a separate program

# examples of similar projects
https://en.wikipedia.org/wiki/Web_hosting_control_panel
https://github.com/topics/control-panel
virtualmin https://github.com/virtualmin/virtualmin-gpl 
webmin https://github.com/webmin/webmin 
- seems to execute subprocesses as unix user using su and uses unix pipes to communicate with processes
- allows users in sudo group to log in via unix
- webmin process runs as root :/
usermin
cpanel
plesk
cockpit https://cockpit-project.org/ https://cockpit-project.org/blog/is-cockpit-secure.html https://github.com/cockpit-project/cockpit
- login with unix user, sudo group not required
- cockpit-session daemon runs as root (only runs whenever a user session is connected)
- webserver runs as cockpit-ws
- each user session is run as that user

https://github.com/hestiacp/hestiacp
https://github.com/itamarjp/yawep - runs commands as web server user, edits text files, etc
https://github.com/gumslone/GumCP - uses ssh to connect, only connects to localhost as one user, stores password in config file (wtf)
https://github.com/adminstock/ssa - same thing as GumCP "All commands are executed via sudo." WTF
https://github.com/Maxelweb/ServerRemoteConsoleSAMP - same fucken thing
https://github.com/netserva/hcp - same shit different project

# FUTURE: transpile to javascript
make sure it complies with libreJS and has permissible license
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