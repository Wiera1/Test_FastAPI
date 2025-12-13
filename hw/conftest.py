import pytest
from main_2 import create_app, db, Client, Parking


@pytest.fixture(scope='session')
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        db.create_all()

        client = Client(
            name='Andrey',
            surname='Veziryan',
            credit_card='1234-5678-9012-3456',
            car_number='A123VE26'
        )
        db.session.add(client)

        parking = Parking(
            address='str. Lenina, 11',
            opened=True,
            count_places=10,
            count_available_places=10,
        )
        db.session.add(parking)
        db.session.commit()

    yield app
    with app.app_context():
        db.create_all()


@pytest.fixture(scope='function')
def client(app):
    app = create_app({'TESTING': True})
    with app.app_context():
        db.create_all()

        yield app.test_client()
        db.session.rollback()
        db.drop_all()


def pytest_configure(config):
    config.addinivalue_line("markers", "parking: test parking")

@pytest.fixture()
def db_session(app):
    with app.app_context():
        db.session.rollback()
        yield db