import pytest
from main_2 import Client, Parking
from factories import ClientFactory, ParkingFactory


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "parking: tests for parking functionality")


@pytest.mark.parametrize('endpoint', [
    "/api/clients",
])
def test_get_methods_return_200(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200


def test_create_client(client):
    data = {
        "name": "Valeriia",
        "surname": "Veziryan",
        "credit_card": "1234-5678-9012-3456",
        "car_number": "C432DC26",
    }
    response = client.post("/api/clients", json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['name'] == "Valeriia"
    assert result['surname'] == "Veziryan"


def test_create_parking(client):
    data = {
        'address': "str. Lenina, 3",
        'count_places': 20,
        'opened': True,
    }
    response = client.post("/api/parkings", json=data)
    assert response.status_code == 201
    result = response.get_json()
    assert result['address'] == "str. Lenina, 3"
    assert result['count_places'] == 20
    assert result['opened'] is True


@pytest.mark.parking
def test_client_entry_success(client):

    client_data = {"name": "Test", "surname": "User", "credit_card": "1111"}
    client.post("/api/clients", json=client_data)

    parking_data = {"address": "Test Parking", "count_places": 5, "opened": True}
    parking_resp = client.post("/api/parkings", json=parking_data)
    parking_id = parking_resp.get_json()['id']

    data = {"client_id": 1, "parking_id": parking_id}
    response = client.post("/api/client_parkings", json=data)
    assert response.status_code == 201


@pytest.mark.parking
def test_client_entry_no_places(client):

    client.post("/api/clients", json={"name": "Test", "surname": "User"})
    parking_resp = client.post("/api/parkings", json={"address": "Test", "count_places": 1, "opened": True})
    parking_id = parking_resp.get_json()['id']

    client.post("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})

    data = {"client_id": 1, "parking_id": parking_id}
    response = client.post("/api/client_parkings", json=data)
    assert response.status_code == 400
    assert "No available places" in response.get_json()['error']


@pytest.mark.parking
def test_client_exit_success(client):

    client.post("/api/clients", json={"name": "Test", "surname": "User", "credit_card": "1111"})
    parking_resp = client.post("/api/parkings", json={"address": "Test", "count_places": 5, "opened": True})
    parking_id = parking_resp.get_json()['id']

    client.post("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})

    response = client.delete("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})
    assert response.status_code == 200
    assert "payment processed" in response.get_json()['message']


@pytest.mark.parking
def test_client_exit_no_card(client):
    parking_resp = client.post("/api/parkings", json={
        "address": "Test",
        "count_places": 5,
        "opened": True})
    parking_id = parking_resp.get_json()['id']

    client_resp = client.post("/api/clients", json={
        "name": "Vova",
        "surname": "Vladimirov"})
    client_id = client_resp.get_json()['id']

    client.post("/api/client_parkings", json={
        "client_id": 2,
        "parking_id": parking_id})

    response = client.delete("/api/client_parkings", json={
        "client_id": client_id,
        "parking_id": parking_id})

    assert response.status_code == 404
    assert "No credit card"
            # in response.get_json()['error'])


@pytest.mark.parking
def test_client_entry_already_parking(client):
    client.post("/api/clients", json={"name": "Test", "surname": "User"})
    parking_resp = client.post("/api/parkings", json={"address": "Test", "count_places": 5, "opened": True})
    parking_id = parking_resp.get_json()['id']

    client.post("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})

    response = client.post("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})
    assert response.status_code == 400
    assert "Client already parked" in response.get_json()['error']


def test_client_exit_already(client):
    client.post("/api/clients", json={"name": "Test", "surname": "User", "credit_card": "1111"})
    parking_resp = client.post("/api/parkings", json={"address": "Test", "count_places": 5, "opened": True})
    parking_id = parking_resp.get_json()['id']

    client.post("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})

    client.delete("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})

    response = client.delete("/api/client_parkings", json={"client_id": 1, "parking_id": parking_id})
    assert response.status_code == 400


def test_create_client_factory(client):
    factory_client = ClientFactory.create()
    client_before = len(Client.query.all())

    data = {
        'name': factory_client.name,
        'surname': factory_client.surname,
        'credit_card': factory_client.credit_card,
        'car_number': factory_client.car_number,
    }

    response = client.post("/api/clients", json=data)
    assert response.status_code == 201

    assert len(Client.query.all()) == client_before + 1
    result = response.get_json()
    assert result['name'] == factory_client.name


# def test_create_client_factory2(client):
#     parking_before = Parking.query.count()
#     factory_parking = ParkingFactory.create()
#
#     data = {
#         'address': factory_parking.address,
#         'count_places': factory_parking.count_places,
#         'opened': factory_parking.opened,
#     }
#
#     response = client.post("/api/clients", json=data)
#     assert response.status_code == 201
#
#     result = response.get_json()
#     assert result['id'] is not None
#     assert result['count_available_places'] == factory_parking.count_places
#     assert Parking.query.count() == parking_before + 1
#

@pytest.mark.parking
def test_create_client_no_card_factory(client):
    factory_client = ClientFactory.build()
    factory_client.credit_card = None

    data = {
        'name': factory_client.name,
        'surname': factory_client.surname,
        'car_number': factory_client.car_number,
    }

    response = client.post("/api/clients", json=data)
    assert response.status_code == 201
    assert response.get_json()['credit_card'] is None