
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
add one-time keys

# client -> server communication
send raw username+password over HTTPS

# FUTURE: async client, transpile to javascript
make sure it complies with libreJS and has permissable license
typescript or coffescript
dart
gwt - google web toolkit (java)
elm or purescript or clojurescript (functional)
webassembly (c/c++/rust/many more, interact with DOM through JS)
	(maybe use SDL with webassembly?)
	https://github.com/shlomnissan/sdl-wasm 
	https://subscription.packtpub.com/book/game_development/9781838644659/1
haxe
any language that can transpile to JS:
https://github.com/jashkenas/coffeescript/wiki/List-of-languages-that-compile-to-JS