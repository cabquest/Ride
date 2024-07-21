from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import JSON, DateTime

db = SQLAlchemy()

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False)
    current_location = db.Column(JSON, nullable = False)
    pick_up_location = db.Column(JSON, nullable = False)
    drop_location = db.Column(JSON, nullable = False)
    pickup_km = db.Column(db.Float, nullable=False)
    total_km = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    fare = db.Column(DECIMAL(10, 2), nullable=False)
    created_at = db.Column(DateTime, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    fullname = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(50), unique = True, nullable = False)
    phone = db.Column(db.String(20), nullable = False)
    is_blocked = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer,nullable=False)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    fullname = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(50), unique = True, nullable = False)
    phone = db.Column(db.String(20), nullable = False)
    is_blocked = db.Column(db.Boolean, default=False)
    driver_id = db.Column(db.Integer,nullable=False)

class Liveloc(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    driver_id = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.String(200), nullable = True)
    longitude = db.Column(db.String(200), nullable = True)