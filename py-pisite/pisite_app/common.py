
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

        # username = session.get("username")
        # session["username"] = username

        return response
    
    def __call__(self):
        return self.as_response()

# can throw json.decoder.JSONDecodeError
def load_data(request):
    data = json.loads(request.data)
    return data

def print_session_cookies():
    print("cookies:")
    for key in flask.session:
        print("{}: {}".format(key, flask.session[key]))

if __name__ == "__main__":
    request = ResponseData(True)
    request.data = "not json"

    test = load_data(request)