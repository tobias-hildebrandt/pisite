
import flask
import json

class ResponseData():
    def __init__(self, success: bool, message: str=None, data:dict=dict()):
        self.success = success
        self.message = message
        if data is None:
            self.data = dict()
        else:
            self.data = data
    
    def as_response(self):
        response: flask.Response = flask.jsonify({
            "success": self.success,
            "message": self.message,
            "data": self.data
        })

        return response
    
    def __call__(self):
        return self.as_response()


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