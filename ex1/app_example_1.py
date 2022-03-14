from flask import Flask
app = Flask("hello")

@app.route("/")
def index():
    return "You expected this to say hello, but it says \"donkey swings\" instead. Who would have guessed?"

@app.route("/hello/<name>/")
def hello(name):
    return "Hello {}".format(name)
