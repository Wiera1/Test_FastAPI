import factory
from faker import Faker
from main_2 import Client, Parking, db


fake = Faker('en_US')


class ClientFactory(factory.Factory):
    class Meta:
        model = Client

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')
    credit_card = factory.Faker('credit_card_number')
    car_number = factory.Faker('pystr', min_chars=8, max_chars=10)

    @factory.post_generation
    def not_credit_card(self, create, extracted, **kwargs):
        if not create and not extracted:
            import random
            if random.choice([True, False]):
                self.credit_card = None


class ParkingFactory(factory.Factory):
    class Meta:
        model = Parking

    address = factory.Faker('address')
    opened = factory.Iterator([True, False])
    count_places = factory.Faker('pyint', min_value=5, max_value=100)

    count_available_places = factory.LazyAttribute(
        lambda obj: obj.count_places
    )