from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    credit_card = db.Column(db.String(50))
    car_number = db.Column(db.String(10))

    parking_session = db.relationship('ClientParking', backref='client', lazy=True)


class Parking(db.Model):
    __tablename__ = 'parking'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False)
    opened = db.Column(db.Boolean, default=False)
    count_places = db.Column(db.Integer, nullable=False)
    count_available_places = db.Column(db.Integer, nullable=False)

    parking_sessions = db.relationship('ClientParking',
                                       backref='parking',
                                       lazy=True)


class ClientParking(db.Model):
    __tablename__ = 'client_parking'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.id'), nullable=False)
    time_in = db.Column(db.DateTime)
    time_out = db.Column(db.DateTime)

    __table_args__ = (
        UniqueConstraint('client_id', 'parking_id', name='unique_client_parking'),
    )

def create_app(config=None):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config:
        app.config.update(config)

    db.init_app(app)

    with app.app_context():
        db.relationship()
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)