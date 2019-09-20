# Todo: Most endpoint ins this file will be readonly when auth is enabled
# Todo: For now we test response == 200, that should by 401 or 401 before we go to production


def test_shops_endpoint_without_auth(client, shop_1):
    response = client.get("/v1/shops", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
    assert json[0]["name"] == "Mississippi"


def test_kinds_endpoint_without_auth(client, kind_1):
    response = client.get("/v1/kinds", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
    assert json[0]["name"] == "Indica"


def test_categories_endpoint_without_auth(client, category_1):
    response = client.get("/v1/categories", follow_redirects=True)
    assert response.status_code == 403


def test_tags_endpoint_without_auth(client, tag_1):
    response = client.get("/v1/tags", follow_redirects=True)
    assert response.status_code == 403


def test_flavors_endpoint_without_auth(client, flavor_1):
    response = client.get("/v1/flavors", follow_redirects=True)
    assert response.status_code == 403


def test_price_endpoint_without_auth(client):
    response = client.get("/v1/prices", follow_redirects=True)
    assert response.status_code == 403


def test_users_endpoint_without_auth(client, member):
    response = client.get("/v1/users", follow_redirects=True)
    assert response.status_code == 403
