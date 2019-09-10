from tests.unit_tests.conftest import MEMBER_EMAIL, MEMBER_PASSWORD, SHOP_EMAIL, SHOP_PASSWORD
from tests.unit_tests.helpers import login, logout


def test_member_login(client, member):
    """Make sure login and logout works."""
    response = login(client, MEMBER_EMAIL, MEMBER_PASSWORD)
    assert response.json["response"]["user"]["authentication_token"]
    assert response.status_code == 200
    logout(client)

    response = login(client, MEMBER_EMAIL, "Wrong password")
    assert response.status_code == 400
    assert response.json["response"]["errors"]["password"] == ["Invalid password"]


def test_unconfirmed_member_login(client, member_unconfirmed):
    """Make sure login shows confirmation error."""
    response = login(client, MEMBER_EMAIL, MEMBER_PASSWORD)
    assert response.json["response"]["errors"]["email"][0] == "Email requires confirmation."
    assert response.status_code == 400


def test_shop_login(client, shop):
    """Make sure login and logout works."""
    response = login(client, SHOP_EMAIL, SHOP_PASSWORD)
    assert response.status_code == 200
    assert response.json["response"]["user"]["authentication_token"]
    logout(client)

    response = login(client, SHOP_EMAIL, "Wrong password")
    assert response.status_code == 400
    assert response.json["response"]["errors"]["password"] == ["Invalid password"]


def test_unconfirmed_shop_login(client, shop_unconfirmed):
    """Make sure login shows confirmation error."""
    response = login(client, SHOP_EMAIL, SHOP_PASSWORD)
    assert response.json["response"]["errors"]["email"][0] == "Email requires confirmation."
    assert response.status_code == 400
