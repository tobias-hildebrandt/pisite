
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
write to text file on change (json format)

# usersfile.txt format:
delimiter is $
line.split('$'):
	0:username
	1:groups, delimited by commands
	2-x: bcrypt password hash
		2:alg (2b)
		3:rounds
		4:salt(22 characters)+hash(everything else)
each line should end with newline (duh?)

# TODO:
create input validator (line + args)
change userfile validator to use line validator

# client -> server communication
send raw username+password over HTTPS