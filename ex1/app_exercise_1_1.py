# Exercise 1.1

from flask import Flask
app = Flask("hello")

@app.route("/")
def index():
    return "How to Use"

@app.route("/add/<float:number_1>/<float:number_2>")
def plus(number_1: float, number_2: float):
    return "Addition result: {}".format(number_1 + number_2)

@app.route("/sub/<float:number_1>/<float:number_2>")
def minus(number_1: float, number_2: float):
    return "Subtraction result: {}".format(number_1 - number_2)

@app.route("/mul/<float:number_1>/<float:number_2>")
def mult(number_1: float, number_2: float):
    return "Multiplication result: {}".format(number_1 * number_2)

@app.route("/div/<float:number_1>/<float:number_2>")
def div(number_1: float, number_2: float):
    if (number_2 != 0):
        return "Division result: {}".format(number_1 / number_2)
    else:
        return "Division result: NaN (division by 0)"