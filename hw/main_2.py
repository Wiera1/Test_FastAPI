from flask import Flask, jsonify, request, Blueprint, abort
from flask_sqlalchemy import SQLAlchemy
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model
else:
    Model = db.Model


class MyModel(Model):
    id = db.Column(db.Integer, primary_key=True)


class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    credit_card = db.Column(db.String(50))
    car_number = db.Column(db.String(10))
    parking_sessions = db.relationship('ClientParking', backref='client', lazy=True)

class Parking(db.Model):
    __tablename__ = 'parking'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False)
    opened = db.Column(db.Boolean, default=False)
    count_places = db.Column(db.Integer, nullable=False)
    count_available_places = db.Column(db.Integer, nullable=False)
    parking_sessions = db.relationship('ClientParking', backref='parking', lazy=True)

class ClientParking(db.Model):
    __tablename__ = 'client_parking'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.id'), nullable=False)
    time_in = db.Column(db.DateTime)
    time_out = db.Column(db.DateTime)
    __table_args__ = (UniqueConstraint('client_id', 'parking_id', name='unique_client_parking'),)

api_bp = Blueprint('api', __name__)

@api_bp.route('/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'surname': c.surname,
        'credit_card': c.credit_card,
        'car_number': c.car_number,
    } for c in clients])

@api_bp.route('/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    # client = Client.query.get_or_404(client_id)
    client = db.session.get(Client, client_id) or abort(404)
    return jsonify({
        'id': client.id, 'name': client.name, 'surname': client.surname,
        'credit_card': client.credit_card, 'car_number': client.car_number,
    })

@api_bp.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json() or {}
    if not all(k in data for k in ['name', 'surname']):
        return jsonify({'error': 'Missing required fields: name, surname'}), 400

    client = Client(
        name=data['name'],
        surname=data['surname'],
        credit_card=data.get('credit_card'),
        car_number=data.get('car_number'),
    )
    db.session.add(client)
    db.session.commit()
    return jsonify({
        'id': client.id, 'name': client.name, 'surname': client.surname,
        'credit_card': client.credit_card, 'car_number': client.car_number,
    }), 201

@api_bp.route('/parkings', methods=['POST'])
def create_parking():
    data = request.get_json() or {}
    if not all(k in data for k in ['address', 'count_places']):
        return jsonify({'error': 'Missing required fields: address, count_places'}), 400

    parking = Parking(
        address=data['address'],
        opened=data.get('opened', False),
        count_places=data['count_places'],
        count_available_places=data['count_places'],
    )
    db.session.add(parking)
    db.session.commit()
    return jsonify({
        'id': parking.id, 'address': parking.address, 'opened': parking.opened,
        'count_places': parking.count_places, 'count_available_places': parking.count_available_places,
    }), 201

@api_bp.route('/client_parkings', methods=['POST'])
def client_entry():
    data = request.get_json() or {}
    if not all(k in data for k in ['client_id', 'parking_id']):
        return jsonify({'error': 'Missing required fields: client_id, parking_id'}), 400

    client = Client.query.get_or_404(data['client_id'])
    parking = Parking.query.get_or_404(data['parking_id'])

    if not parking.opened:
        return jsonify({'error': 'Parking is closed'}), 400

    if parking.count_available_places <= 0:
        return jsonify({'error': 'No available places'}), 400

    existing_session = ClientParking.query.filter_by(
        client_id=data['client_id'],
        parking_id=data['parking_id']
    ).first()

    if existing_session and not existing_session.time_out:
        return jsonify({'error': 'Client already parked'}), 400

    if existing_session:
        existing_session.time_in = datetime.now()
    else:
        session = ClientParking(
            client_id=data['client_id'],
            parking_id=data['parking_id'],
            time_in=datetime.now(),
        )
        db.session.add(session)

    parking.count_available_places -= 1
    db.session.commit()
    return jsonify({'message': 'Client entered parking'}), 201

@api_bp.route('/client_parkings', methods=['DELETE'])
def client_exit():
    data = request.get_json() or {}
    if not all(k in data for k in ['client_id', 'parking_id']):
        return jsonify({'error': 'Missing required fields: client_id, parking_id'}), 400

    session = ClientParking.query.filter_by(
        client_id=data['client_id'],
        parking_id=data['parking_id'],
    ).first_or_404()

    if session.time_out:
        return jsonify({'error': 'Client already left parking'}), 400

    client = session.client
    if not client.credit_card:
        return jsonify({'error': 'No credit card attached to client'}), 400

    session.time_out = datetime.now()
    session.parking.count_available_places += 1
    db.session.commit()

    duration = (session.time_out - session.time_in).total_seconds() / 60
    return jsonify({
        'message': 'Client left parking, payment processed',
        'duration_minutes': round(duration, 2),
    })

def create_app(config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' if config and config.get('TESTING') else 'sqlite:///parking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if config:
        app.config.update(config)

    db.init_app(app)
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
