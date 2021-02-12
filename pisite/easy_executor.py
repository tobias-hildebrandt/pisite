
import os
import sys
import subprocess
import logging
import shlex
import json


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s : %(message)s")
console_handler.setFormatter(formatter)
_logger.addHandler(console_handler)

VALIDATION_TABLE_PATH_RELATIVE = ".pisite/validationtable.json"
NOT_VALID_COMMAND = "INVALID_COMMAND"
LOGIN_SUCCESS_STRING = "LOGIN_SUCCESS"
TIMEOUT = 5 # timeout for command execution in seconds

class Error(Exception):
    pass

class InvalidCommand(Error):
    pass

def check_login(username, password) -> bool:
    try:
        result = run_as(username, password, None)
        _logger.info("login result: {}".format(result))
        (out, _, _) = result
        return LOGIN_SUCCESS_STRING in out
    except:
        return False

def get_valid_scripts(username) -> list:
    absolute_filepath_to_validation_table = os.path.join(os.path.expanduser("~{}".format(username)), VALIDATION_TABLE_PATH_RELATIVE)
    with open(absolute_filepath_to_validation_table, 'r') as f:
        validation_table = json.load(f)

    scripts = list(validation_table)

    return scripts

def run_as(username, password, command) -> dict:
    """
    Executes a command as user, given a password
    TimeoutExpired
    JSONDecodeError
    OSError
    """
    _logger.info("username is {}".format(username))
    #_logger.info("password is {}".format(password))
    _logger.info("command is {}".format(command))

    os.chdir(os.path.expanduser("~{}".format(username))) # go to user's home directory
    #_logger.info("cwd is {}".format(os.getcwd()))
    
    # decode validation table
    # this is done as calling user
    absolute_filepath_to_validation_table = os.path.join(os.path.expanduser("~{}".format(username)), VALIDATION_TABLE_PATH_RELATIVE)
    with open(absolute_filepath_to_validation_table, 'r') as f:
        validation_table = json.load(f)

    # set the execution path prefix, this is where all scripts exist
    execution_path_prefix = os.path.join(absolute_filepath_to_validation_table, os.path.pardir)
    
    if command is not None:
        # tokens[0] must be KEY in validation table
        # tokens[1:] are arguments 
        # split line into tokens
        exec_cmd = shlex.split(command)

        # make sure first token is a KEY in validation table
        if exec_cmd[0] not in validation_table:
            _logger.info("not allowed {}".format(command))
            raise InvalidCommand # exit function

        # replace relative (to script dir) path with absolute script path 
        exec_cmd[0] = os.path.abspath(os.path.join(execution_path_prefix, validation_table[exec_cmd[0]]))

        _logger.info("exec_cmd is {}".format(exec_cmd))
    elif command is None:
        # given None
        # tell the subprocess to echo login success, which we filter for in check_login 
        exec_cmd = shlex.split("echo {}".format(LOGIN_SUCCESS_STRING))
    
    # -l act as login shell
    # -c execute command
    command_as_user = "su {} -l -c".format(username)
    args = shlex.split(command_as_user)
    args.append(" ".join(exec_cmd))

    _logger.info("args is {}".format(args))

    completed = subprocess.run(args=args, input=password+"\n", timeout=TIMEOUT, capture_output=True, text=True)

    # strip out first line of stderr
    return (completed.returncode, completed.stdout, "\n".join(completed.stderr.split("\n")[1:]))

if __name__ == "__main__":
    username = "testuser"
    password = "testpassword"

    results = check_login(username, password)
    print(results)
    print()

    results = run_as(username, password, "TEST_ECHO 123 132 123")
    print(results)
    print()

    try:
        results = run_as(username, password, "echo $USER\'; echo hello\'")
        print(results)
    except InvalidCommand:
        print("command was invalid")
    
    print()

