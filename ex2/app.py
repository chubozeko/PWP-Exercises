import json
from urllib import response
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.exceptions import UnsupportedMediaType, NotFound, Conflict, BadRequest
from werkzeug.routing import BaseConverter
from datetime import datetime

JSON = "application/json"

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

api = Api(app)
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


deployments = db.Table(
    "deployments",
    db.Column("deployment_id", db.Integer, db.ForeignKey("deployment.id"), primary_key=True),
    db.Column("sensor_id", db.Integer, db.ForeignKey("sensor.id"), primary_key=True)
)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    altitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(256), nullable=True)

    sensor = db.relationship("Sensor", back_populates="location", uselist=False)

    def serialize(self, short_form=False):
        doc = {
            "name": self.name
        }
        if not short_form:
            doc["longitude"] = self.longitude
            doc["latitude"] = self.latitude
            doc["altitude"] = self.altitude
            doc["description"] = self.description
        return doc

    def deserialize(self, doc):
        self.name = doc["name"]
        self.latitude = doc.get("latitude")
        self.longitude = doc.get("longitude")
        self.altitude = doc.get("altitude")
        self.description = doc.get("description")


class Deployment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(128), nullable=False)

    sensors = db.relationship("Sensor", secondary=deployments, back_populates="deployments")


class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    model = db.Column(db.String(128), nullable=False)
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.id"),
        unique=True, nullable=True
    )

    location = db.relationship("Location", back_populates="sensor")
    measurements = db.relationship("Measurement", back_populates="sensor")
    deployments = db.relationship("Deployment", secondary=deployments, back_populates="sensors")

    def serialize(self, short_form=False):
        return {
            "name": self.name,
            "model": self.model,
            "location": self.location and self.location.serialize(short_form=short_form)
        }

    def deserialize(self, doc):
        self.name = doc["name"]
        self.model = doc["model"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["name", "model"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Sensor's unique name",
            "type": "string"
        }
        props["model"] = {
            "description": "Name of the sensor's model",
            "type": "string"
        }
        return schema


class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensor.id", ondelete="SET NULL"))
    value = db.Column(db.Float, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    sensor = db.relationship("Sensor", back_populates="measurements")

    def deserialize(self, dic):
        self.value = dic["value"]
        self.time = datetime.fromisoformat(dic["time"])

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["value", "time"]
        }
        props = schema["properties"] = {}
        props["value"] = {
            "description": "Measurements' value",
            "type": "number"
        }
        props["time"] = {
            "description": "time of measurements",
            "type": "string",
            "format": "date-time"

        }
        return schema


class SensorConverter(BaseConverter):

    def to_python(self, sensor_name):
        db_sensor = Sensor.query.filter_by(name=sensor_name).first()
        if db_sensor is None:
            raise NotFound
        return db_sensor

    def to_url(self, db_sensor):
        return db_sensor.name


class SensorCollection(Resource):

    def get(self):
        body = {"items": []}
        for db_sensor in Sensor.query.all():
            item = db_sensor.serialize(short_form=True)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=JSON)

    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Sensor.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        sensor = Sensor()
        sensor.deserialize(request.json)

        try:
            db.session.add(sensor)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                "Sensor with name '{name}' already exists.".format(
                    **request.json
                )
            )

        return Response(
            status=201, headers={"Location": api.url_for(SensorItem, sensor=sensor)}
        )


class SensorItem(Resource):

    def get(self, sensor):
        body = sensor.serialize()
        return Response(json.dumps(body), 200, mimetype=JSON)

    def put(self, sensor):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Sensor.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        sensor.deserialize(request.json)
        try:
            db.session.add(sensor)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                "Sensor with name '{name}' already exists.".format(
                    **request.json
                )
            )

        return Response(status=204)

    def delete(self, sensor):
        db.session.delete(sensor)
        db.session.commit()
        return Response(status=204)


class LocationItem(Resource):

    def get(self, location):
        pass


class MeasurementItem(Resource):

    def get(self, sensor, measurement):
        pass

    def delete(self, sensor, measurement):
        pass


class MeasurementCollection(Resource):

    def get(self, sensor):
        pass

    def post(self, sensor):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Measurement.json_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e))

        measurement = Measurement()
        measurement.deserialize(request.json)
        try:
            db.session.add(measurement)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                "Sensor with name '{name}' already exists.".format(
                    **request.json
                )
            )

        return Response(
            status=201, headers={"Location": api.url_for(MeasurementItem, sensor=sensor, measurement=measurement.id)}
        )


app.url_map.converters["sensor"] = SensorConverter
api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(SensorItem, "/api/sensors/<sensor:sensor>/")
api.add_resource(MeasurementCollection, "/api/sensors/<sensor:sensor>/measurements/")
api.add_resource(MeasurementItem, "/api/sensors/<sensor:sensor>/measurements/<int:measurement>/")
