import datetime
import os
import uuid
from contextlib import closing

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

from server.database import Category, Flavor, Kind, Price, Role, Shop, Tag, User, db, user_datastore

MEMBER_EMAIL = "member@example.com"
MEMBER_PASSWORD = "Membertje"
SHOP_EMAIL = "shop@example.com"
SHOP_PASSWORD = "Shopje"


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
    from main import app

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
    roles = ["member", "shop", "admin"]
    [db.session.add(Role(id=str(uuid.uuid4()), name=role)) for role in roles]
    db.session.commit()


@pytest.fixture
def member_unconfirmed(user_roles):
    user = user_datastore.create_user(username="member", password=MEMBER_PASSWORD, email=MEMBER_EMAIL)
    user_datastore.add_role_to_user(user, "member")
    db.session.commit()
    return user


@pytest.fixture
def member(member_unconfirmed):
    user = User.query.filter(User.email == MEMBER_EMAIL).first()
    user.confirmed_at = datetime.datetime.utcnow()
    db.session.commit()
    return user


@pytest.fixture
def member_logged_in(member):
    user = User.query.filter(User.email == MEMBER_EMAIL).first()
    # Todo: actually login/handle cookie
    db.session.commit()
    return user


@pytest.fixture
def shop_unconfirmed(user_roles):
    user = user_datastore.create_user(username="shop", password=SHOP_PASSWORD, email=SHOP_EMAIL)
    user_datastore.add_role_to_user(user, "shop")
    db.session.commit()
    return user


@pytest.fixture
def shop(shop_unconfirmed):
    user = User.query.filter(User.email == SHOP_EMAIL).first()
    user.confirmed_at = datetime.datetime.utcnow()
    db.session.commit()
    return user


@pytest.fixture
def teacher_logged_in(teacher):
    user = User.query.filter(User.email == SHOP_EMAIL).first()
    # Todo: actually login/handle cookie
    # db.session.commit()
    return user


@pytest.fixture
def price_1():
    fixture = Price(
        id=str(uuid.uuid4()), internal_product_id="1", half=4.5, one=8, two_five=19, five=36, joint=4.0, piece=None
    )
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_1():
    fixture = Shop(id=str(uuid.uuid4()), name="Mississippi", description="Shop descciption")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def shop_2():
    fixture = Shop(id=str(uuid.uuid4()), name="Head Shop", description="Shop descciption 2")
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def category_1(shop_1):
    fixture = Category(id=str(uuid.uuid4()), name="Category 1", description="Category descciption", shop_id=shop_1.id)
    db.session.add(fixture)
    db.session.commit()
    return fixture


@pytest.fixture
def category_2(shop_1):
    fixture = Category(id=str(uuid.uuid4()), name="Category 2", description="Category descciption 2", shop_id=shop_1.id)
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
def kind_1():
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
    # record = KindToTag(id=str(uuid.uuid4()), kind_id=fixture_id, tag=tag_1, amount=90)
    # db.session.add(record)
    # record = KindToTag(id=str(uuid.uuid4()), kind_id=fixture_id, tag_id=tag_2, amount=60)
    # db.session.add(record)
    # record = KindToFlavor(id=str(uuid.uuid4()), kind_id=fixture_id, flavor_id=flavor_1.id)
    # db.session.add(record)
    # record = KindToFlavor(id=str(uuid.uuid4()), kind_id=fixture_id, flavor_id=flavor_2.id)
    # db.session.add(record)
    db.session.commit()
    return fixture


# @pytest.fixture
# def exercise_1(teacher, riff, riff_multi_chord, riff_without_chord_info, riff_without_chord):
#     exercise_id = str(uuid.uuid4())
#     riff_exercise = RiffExercise(
#         id=exercise_id,
#         name="Exercise 1",
#         description="Some description",
#         root_key="c",
#         instrument_key="c",
#         is_public=True,
#         is_copyable=True,
#         # starts=3,
#         created_by=teacher.id
#     )
#     db.session.add(riff_exercise)
#     record = RiffExerciseItem(id=str(uuid.uuid4()), riff_id=riff.id, riff_exercise_id=exercise_id,
#                               number_of_bars=riff.number_of_bars, chord_info=riff.chord_info,
#                               pitch="c", octave=0, order_number=0)
#     db.session.add(record)
#     db.session.commit()
#     return riff_exercise
#
#
# @pytest.fixture
# def exercise_2(teacher, riff, riff_multi_chord, riff_without_chord_info, riff_without_chord):
#     riff_exercise = RiffExercise(
#         id=str(uuid.uuid4()),
#         name="Exercise 1",
#         description="Some description",
#         root_key="c",
#         instrument_key="c",
#         is_public=True,
#         is_copyable=True,
#         # starts=3,
#         created_by=teacher.id
#     )
#     db.session.add(riff_exercise)
#     db.session.commit()
#     return riff_exercise
