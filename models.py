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
    payment_status = db.Column(db.String(20), nullable = True)
    payment_type = db.Column(db.String(50), nullable = True)
    created_at = db.Column(DateTime, nullable=False)
    salary_status = db.Column(db.String(20), nullable = True)

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

class CancelReason(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    ride_id = db.Column(db.Integer, nullable = False)
    reason = db.Column(db.String(200), nullable = False)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    driver_id = db.Column(db.Integer, nullable = False)
    ride_id = db.Column(db.Integer, nullable = False)
    date = db.Column(DateTime, nullable=False)
    incentive = db.Column(DECIMAL(10, 2), nullable=True) 
    deduction = db.Column(DECIMAL(10, 2), nullable=True) 
    amount = db.Column(DECIMAL(10, 2), nullable=False)  