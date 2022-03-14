from flask import Flask, request

app = Flask("hello")

@app.route("/")
def index():
    return "You expected this to say hello, but it says \"donkey swings\" instead. Who would have guessed?"

@app.route("/hello/")
def hello():
    try:
        name = request.args["name"]
    except KeyError:
        return "Missing query parameter: name", 400
    return "Hello {}".format(name)
