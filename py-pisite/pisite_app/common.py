
import flask
import json
import functools
from dataclasses import dataclass, field, asdict, is_dataclass, fields, MISSING
from typing import List, Dict

# function decorator that jsonifies dataclasses via dataclasses.asdict
def jsonify_if_dataclass(func):
    @functools.wraps(func)
    def wrapped_func(**kwargs):
        result = func(**kwargs)
        if is_dataclass(result):
            return flask.jsonify(asdict(result))
        else:
            return result
    return wrapped_func

## to serialize these classes, use dataclasses.asdict or jsonify_response
@dataclass
class DataLine():
    name: str 
    data: str

@dataclass
class Endpoint():
    name: str
    url: str

# general response, jsonify success, message, data
@dataclass
class ResponseData():
    success: bool 
    message: str = field(default_factory=str)
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.message is "":
            self.message = None
        if self.data is None:
            self.data = dict()

# response to a GET on a server/power endpoint
@dataclass
class StatusResponse():
    any_power: bool
    statuses: Dict[str, bool] = field(default_factory=dict)
    info: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if self.statuses is None:
            self.statuses = dict()
        if self.info is None:
            self.info = dict()

##

def print_session_values():
    print("session:", end=" ")
    for key in flask.session:
        print("{}: {}".format(key, flask.session[key]), end=", ")
    print()

def print_request_headers():
    print("headers:", end=" ")
    for header in flask.request.headers:
        print(header, end=", ")
    print()