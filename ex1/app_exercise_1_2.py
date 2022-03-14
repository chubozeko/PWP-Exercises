# Exercise 1.2
import math

from flask import Flask, request

app = Flask("hello")

@app.route("/")
def index():
    return "How to use: \n TODO"

@app.route("/trig/<func>/")
def trig(func):
    try:
        angle = request.args["angle"]
        if (angle.isnumeric()):
            try:
                unit = request.args["unit"]
                if (unit == "degree"):
                    x = math.radians(float(angle))
                elif (unit == "radian"):
                    x = float(angle)
                else:
                    return "Invalid query parameter value for 'unit'", 400
            except KeyError:
                x = float(angle)

            if (func == "sin"):
                return "Sine result: {:.3f}".format(math.sin(x))
            elif (func == "cos"):
                return "Cosine result: {:.3f}".format(math.cos(x))
            elif (func == "tan"):
                return "Tangent result: {:.3f}".format(math.tan(x))
            else:
                return "Operation not found: {}".format(func), 404
        else:
            return "Invalid query parameter value(s) for 'angle'", 400
    except KeyError:
        return "Invalid query parameter value(s) for 'angle'", 400

