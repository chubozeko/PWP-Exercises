import json
from datetime import datetime
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.exceptions import abort

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    location = db.Column(db.String(64), nullable=False)

    product = db.relationship("Product", back_populates="in_storage")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(64), nullable=False, unique=True)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    in_storage = db.relationship("StorageItem", back_populates="product")

@app.route("/products/add/", methods=["POST"])
def add_product():
    if request.method == "POST":
        try:
            try:
                weight = float(request.json["weight"])
                price = float(request.json["price"])
            except (ValueError):
                return "Weight and price must be numbers", 400

            handle = request.json["handle"]
            check_handle = Product.query.filter_by(handle=handle).first()
            if check_handle:
                return "Handle already exists", 409
            else:
                prod = Product(
                    handle=handle,
                    weight=weight,
                    price=price
                )
                db.session.add(prod)
                db.session.commit()
                return "Success", 201
        except:
            return "Request content type must be JSON", 415
    else:
         return "POST method required", 405

@app.route("/storage/<product>/add/", methods=["POST"])
def add_to_storage(product):
    if request.method == "POST":
        check_product = Product.query.filter_by(handle=product).first()
        if check_product:
            product_id = Product.query.filter_by(handle=product).first().id
            location = request.json["location"]
            qty = request.json["qty"]
            if location == None or qty == None:
                return "Request content type must be JSON",415
            if not isinstance(qty, int):
                return "Qty must be an integer", 400
            store = StorageItem(
                product_id = product_id,
                location = location,
                qty = qty
            )
            db.session.add(store)
            db.session.commit()
            return "Success", 201
        else:
            return "Product not found", 404
    else:
        return "POST method required", 405


@app.route("/storage/", methods=["GET"])
def get_inventory():
    if request.method == "GET":
        jsonOut = []
        out = {}
        subOut = []
        for product in Product.query.all():
            out["handle"] = product.handle
            out["weight"] = product.weight
            out["price"] = product.price
            for storage in StorageItem.query.filter_by(product_id = product.id).all():
                subOut.append((storage.location, storage.qty))
            out["inventory"] = subOut
            jsonOut.append(out)
            out = {}
            subOut = []
        return json.dumps(jsonOut), 200
    else:
        return "GET method required", 405


# @app.route("/<sensor_name>/measurements/add/", methods=["POST"])
# def add_measurement(sensor_name):
#     # This branch happens when user submits the form
#     try:
#         sensor = Sensor.query.filter_by(name=sensor_name).first()
#         if sensor:
#             value = float(request.json["value"])
#             meas = Measurement(
#                 sensor=sensor,
#                 value=value,
#                 time=datetime.now()
#             )
#             db.session.add(meas)
#             db.session.commit()
#         else:
#             abort(404)
#     except (KeyError, ValueError, IntegrityError):
#         abort(400)