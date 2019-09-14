def test_shops_list_endpoint(client, shop_1):
    response = client.get(f"/v1/shops", follow_redirects=True)
    assert response.status_code == 200


def test_shops_create_endpoint(client):
    data = {"name": "Naampje", "description": "Description"}
    response = client.post(f"/v1/shops", json=data, follow_redirects=True)
    assert response.status_code == 401
