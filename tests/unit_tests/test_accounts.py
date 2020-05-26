from tests.unit_tests.conftest import CUSTOMER_EMAIL, CUSTOMER_PASSWORD, EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD
from tests.unit_tests.helpers import login, logout


def test_customer_login(client, customer):
    """Make sure login and logout works."""
    response = login(client, CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
    # assert response.json["response"]["user"]["authentication_token"]
    assert response.status_code == 200
    logout(client)

    response = login(client, CUSTOMER_EMAIL, "Wrong password")
    assert response.status_code == 400
    assert response.json["response"]["errors"]["password"] == ["Invalid password"]


def test_unconfirmed_customer_login(client, customer_unconfirmed):
    """Make sure login shows confirmation error."""
    response = login(client, CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
    assert response.json["response"]["errors"]["email"][0] == "Email requires confirmation."
    assert response.status_code == 400


def test_employee_login(client, employee):
    """Make sure login and logout works."""
    response = login(client, EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)
    assert response.status_code == 200
    # assert response.json["response"]["user"]["authentication_token"]
    logout(client)

    response = login(client, EMPLOYEE_EMAIL, "Wrong password")
    assert response.status_code == 400
    assert response.json["response"]["errors"]["password"] == ["Invalid password"]


def test_unconfirmed_employee_login(client, employee_unconfirmed):
    """Make sure login shows confirmation error."""
    response = login(client, EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD)
    assert response.json["response"]["errors"]["email"][0] == "Email requires confirmation."
    assert response.status_code == 400
