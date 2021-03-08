from flask_login import UserMixin
from datetime import datetime
from config import db


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    permissions = db.Column(db.String(512), nullable=False)

    users = db.relationship('User', backref='role_u')


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True)
    login = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    role = db.Column(db.Integer, db.ForeignKey('roles.id'))


class Machine(db.Model):
    __tablename__ = 'machines'
    machineID = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)

    telemetries = db.relationship('Telemetry', backref='machine')
    errors = db.relationship('Error', backref='machine')
    failures = db.relationship('Failure', backref='machine')
    maints = db.relationship('Maint', backref='machine')
    predicts = db.relationship('PredictedFailure', backref='machine')


class Telemetry(db.Model):
    __tablename__ = 'telemetry'
    datetime = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    machineID = db.Column(db.Integer, db.ForeignKey('machines.machineID'))
    volt = db.Column(db.Float, nullable=False)
    rotate = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    vibration = db.Column(db.Float, nullable=False)


class Error(db.Model):
    __tablename__ = 'errors'
    datetime = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    machineID = db.Column(db.Integer, db.ForeignKey('machines.machineID'))
    errorID = db.Column(db.String(50), nullable=False)


class Failure(db.Model):
    __tablename__ = 'failures'
    datetime = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    machineID = db.Column(db.Integer, db.ForeignKey('machines.machineID'))
    failure = db.Column(db.String(50), nullable=False)


class Maint(db.Model):
    __tablename__ = 'maints'
    datetime = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    machineID = db.Column(db.Integer, db.ForeignKey('machines.machineID'))
    comp = db.Column(db.String(50), nullable=False)


class Request(db.Model):
    __tablename__ = 'requests'
    name = db.Column(db.String(50), primary_key=True)
    text = db.Column(db.String(512), nullable=False)


class PredictedFailure(db.Model):
    __tablename__ = 'predicted'
    date = db.Column(db.String(50), primary_key=True)
    machineID = db.Column(db.Integer, db.ForeignKey('machines.machineID'))
    predict = db.Column(db.String(50), nullable=False)
