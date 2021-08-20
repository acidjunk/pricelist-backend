import datetime
import json
import os
import uuid
from contextlib import closing

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from server.database import (
    Category,
    Flavor,
    Kind,
    KindToFlavor,
    KindToStrain,
    KindToTag,
    Order,
    Price,
    Product,
    Role,
    Shop,
    ShopToPrice,
    Strain,
    Tag,
    User,
    db,
    user_datastore,
)

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Adminnetje"
CUSTOMER_EMAIL = "customer@example.com"
CUSTOMER_PASSWORD = "Customertje"
EMPLOYEE_EMAIL = "employee@example.com"
EMPLOYEE_PASSWORD = "Employeetje"


@pytest.fixture(scope="session")
def database(db_uri):
    """Create and drop test database for a pytest worker."""
    url = make_url(db_uri)
    db_to_create = url.database

    # database to connect to for creating `db_to_create`.
    url.database = "postgres"
    engine = create_engine(str(url))

    with closing(engine.connect()) as conn:
        print(f"Drop and create {db_to_create}")
        # Can't drop or create a database from within a transaction; end transaction by committing.
        conn.execute("COMMIT;")
        conn.execute(f'DROP DATABASE IF EXISTS "{db_to_create}";')
        conn.execute("COMMIT;")
        conn.execute(f'CREATE DATABASE "{db_to_create}";')
        print(f"Drop and create done for {db_to_create}")
    yield database


@pytest.fixture(scope="session")
def db_uri(worker_id):
    """Ensure that every py.test workerthread uses a own DB, when running the test suite with xdist and `-n auto`."""
    database_uri = "postgresql://pricelist:pricelist@localhost/pricelist-test"
    if os.getenv("DB_USER"):
        print("Running with TRAVIS!")
        database_uri = "postgresql://postgres:@localhost/pricelist-test"
    if worker_id == "master":
        # pytest is being run without any workers
        print(f"USING DB CONN: {database_uri}")
        return database_uri
    # using xdist setup
    url = make_url(database_uri)
    url.database = f"{url.database}-{worker_id}"
    print(f"USING DB CONN: {url}")
    return str(url)


@pytest.fixture(scope="function")
def app(database):
    """
    Create a Flask app context for the tests.
    """
    from server.main import app

    with app.app_context():
        db.init_app(app)
        db.create_all()
        # migrate = Migrate(app, db)
        # api.init_app(app)

    yield app

    with app.app_context():
        # clean up : revert DB to a clean state
        db.session.remove()
        db.session.commit()
        db.session.close_all()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def user_roles():
    roles = ["customer", "employee", "admin"]
    [db.session.add(Role(id=str(uuid.uuid4()), name=role)) for role in roles]
    db.session.commit()


@pytest.fixture
def customer_unconfirmed(user_roles):
    user = user_datastore.create_user(username="customer", password=CUSTOMER_PASSWORD, email=CUSTOMER_EMAIL)
    user_datastore.add_role_to_user(user, "customer")
    db.session.commit()
    return user


@pytest.fixture
def customer(customer_unconfirmed):
    user = User.query.filter(User.email == CUSTOMER_EMAIL).first()
    user.confirmed_at = datetime.datetime.utcnow()
    db.session.commit()
    return user


@pytest.fixture
def admin(user_roles):
    user = user_datastore.create_user(username="admin", password=ADMIN_PASSWORD, email=ADMIN_EMAIL)
    user_datastore.add_role_to_user(user, "admin")
    user.confirmed_at = datetime.datetime.utcnow()
    db.session.commit()
    return user


@pytest.fixture
def admin_logged_in(admin):
    user = User.query.filter(User.email == ADMIN_EMAIL).first()
    # Todo: actually login/handle cookie
    db.session.commit()
    return user


@pytest.fixture
def customer_logged_in(customer):
    user = User.query.filter(User.email == CUSTOMER_EMAIL).first()
    # Todo: actually login/handle cookie
    db.session.commit()
    return user


@pytest.fixture
def employee_unconfirmed(user_roles):
    user = user_datastore.create_user(username="employee", password=EMPLOYEE_PASSWORD, email=EMPLOYEE_EMAIL)
    user_datastore.add_role_to_user(user, "employee")
    db.session.commit()
    return user


@pytest.fixture
def employee(employee_unconfirmed):
    user = User.query.filter(User.email == EMPLOYEE_EMAIL).first()
    user.confirmed_at = datetime.datetime.utcnow()
    db.session.commit()
    return user


@pytest.fixture
def price_1():
    fixture = Price(id=str(uuid.uuid4()), internal_product_id="01", half="5.50", one="10.0", five="45.0", joint="4.50")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def price_2():
    fixture = Price(id=str(uuid.uuid4()), internal_product_id="02", one="7.50", five="35.0", joint="4.00")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def price_3():
    fixture = Price(id=str(uuid.uuid4()), internal_product_id="03", piece="2.50")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_1():
    fixture = Shop(id=str(uuid.uuid4()), name="Mississippi", description="Shop description")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_2():
    fixture = Shop(id=str(uuid.uuid4()), name="Head Shop", description="Shop description 2")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_with_whitelist():
    fixture = Shop(id="f5054538-d739-4b24-aaeb-db096d09279a", name="Head Shop", description="Shop description 2")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def category_1(shop_1):
    fixture = Category(id=str(uuid.uuid4()), name="Category 1", description="Category description", shop_id=shop_1.id)
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def category_2(shop_1):
    fixture = Category(id=str(uuid.uuid4()), name="Category 2", description="Category description 2", shop_id=shop_1.id)
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def tag_1():
    fixture = Tag(id=str(uuid.uuid4()), name="Giggly")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def tag_2():
    fixture = Tag(id=str(uuid.uuid4()), name="Focused")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def flavor_1():
    fixture = Flavor(id=str(uuid.uuid4()), name="Lemon", icon="lemon", color="ff0000")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def flavor_2():
    fixture = Flavor(id=str(uuid.uuid4()), name="Earth", icon="earth", color="00ff00")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def strain_1():
    fixture = Strain(id=str(uuid.uuid4()), name="Haze")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def strain_2():
    fixture = Strain(id=str(uuid.uuid4()), name="Kush")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def kind_1(tag_1, flavor_1, strain_1):
    fixture_id = str(uuid.uuid4())
    fixture = Kind(
        id=fixture_id,
        name="Indica",
        c=False,
        h=False,
        i=True,
        s=False,
        short_description_nl="Cinderela 99 x Jack Herrer",
        description_nl="Amnesia is typisch een sativa-dominant cannabis strain, met wat variaites tussen de kwekers. "
        "Cinderela 99 x Jack Herrer in de volksmond ook wel bekend als Haze knalt.",
        short_description_en="Amnesia is typically a sativa-dominant cannabis strain",
        description_en="Amnesia is typically a sativa-dominant cannabis strain with some variation between breeders. "
        "Skunk, Cinderella 99, and Jack Herer are some of Amnesia’s genetic forerunners, passing on "
        "uplifting, creative, and euphoric effects. This strain normally has a high THC and low CBD "
        "profile and produces intense psychotropic effects that new consumers should be wary of.",
    )
    db.session.add(fixture)
    record = KindToTag(id=str(uuid.uuid4()), kind_id=fixture_id, tag=tag_1, amount=90)
    db.session.add(record)
    record = KindToFlavor(id=str(uuid.uuid4()), kind_id=fixture_id, flavor_id=flavor_1.id)
    db.session.add(record)
    record = KindToStrain(id=str(uuid.uuid4()), kind_id=fixture_id, strain_id=strain_1.id)
    db.session.add(record)
    db.session.commit()
    return fixture


@pytest.fixture
def kind_2():
    fixture_id = str(uuid.uuid4())
    fixture = Kind(
        id=fixture_id,
        name="Sativa",
        c=False,
        h=False,
        i=False,
        s=True,
        short_description_nl="Vet goeie indica",
        description_nl="Deze knalt er echt in. Alleen voor ervaren gebruikers.",
        short_description_en="Really good indica",
        description_en="This one will blow your mind. Only for experienced users.",
    )
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def product_1():
    fixture_id = str(uuid.uuid4())
    fixture = Product(
        id=fixture_id,
        name="Cola",
        short_description_nl="Cola Light",
        description_nl="Deze knalt er echt in. Alleen voor echte caffeine addicts.",
        short_description_en="Cola Light",
        description_en="This one will blow your mind. Only for Real caffeine addicts.",
    )
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_with_products(shop_1, kind_1, kind_2, price_1, price_2, price_3, product_1):
    shop_to_price1 = ShopToPrice(price_id=price_1.id, shop_id=shop_1.id, kind_id=kind_1.id)
    shop_to_price2 = ShopToPrice(price_id=price_2.id, shop_id=shop_1.id, kind_id=kind_2.id)
    shop_to_price3 = ShopToPrice(price_id=price_3.id, shop_id=shop_1.id, product_id=product_1.id)
    db.session.add(shop_to_price1)
    db.session.add(shop_to_price2)
    db.session.add(shop_to_price3)
    db.session.commit()
    return shop_1


@pytest.fixture
def shop_with_orders(shop_with_products, kind_1, kind_2, price_1, price_2):
    items = [
        {
            "description": "1 gram",
            "price": price_1.one,
            "kind_id": str(kind_1.id),
            "kind_name": kind_1.name,
            "internal_product_id": "01",
            "quantity": 2,
        },
        {
            "description": "1 joint",
            "price": price_2.joint,
            "kind_id": str(kind_2.id),
            "kind_name": kind_2.name,
            "internal_product_id": "02",
            "quantity": 1,
        },
    ]
    order = Order(
        id=str(uuid.uuid4()),
        shop_id=str(shop_with_products.id),
        order_info=json.dumps(items),
        total=24.0,
        customer_order_id=1,
    )
    db.session.add(order)
    order = Order(
        id=str(uuid.uuid4()),
        shop_id=str(shop_with_products.id),
        order_info=json.dumps(items),
        total=24.0,
        customer_order_id=2,
        completed_at=datetime.datetime.utcnow(),
        status="complete",
    )
    db.session.add(order)
    db.session.commit()
    return shop_1


@pytest.fixture
def shop_with_mixed_orders(shop_with_products, kind_1, kind_2, price_1, price_2, price_3, product_1):
    items = [
        {
            "description": "1 gram",
            "price": price_1.one,
            "kind_id": str(kind_1.id),
            "kind_name": kind_1.name,
            "internal_product_id": "01",
            "quantity": 2,
        },
        {
            "description": "1 joint",
            "price": price_2.joint,
            "kind_id": str(kind_2.id),
            "kind_name": kind_2.name,
            "internal_product_id": "02",
            "quantity": 1,
        },
        {
            "description": "1 cola",
            "price": price_3.piece,
            "price_id": str(product_1.id),
            "price_name": product_1.name,
            "internal_product_id": "03",
            "quantity": 1,
        },
    ]
    order = Order(
        id=str(uuid.uuid4()),
        shop_id=str(shop_with_products.id),
        order_info=json.dumps(items),
        total=26.50,
        customer_order_id=1,
    )
    db.session.add(order)
    order = Order(
        id=str(uuid.uuid4()),
        shop_id=str(shop_with_products.id),
        order_info=json.dumps(items),
        total=26.50,
        customer_order_id=2,
        completed_at=datetime.datetime.utcnow(),
        status="complete",
    )
    db.session.add(order)
    db.session.commit()
    return shop_1
