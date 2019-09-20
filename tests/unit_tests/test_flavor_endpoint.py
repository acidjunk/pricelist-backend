def test_flavors_list_endpoint(client, flavor_1):
    response = client.get(f"/v1/flavors", follow_redirects=True)
    assert response.status_code == 403


def test_flavors_create_endpoint(client):
    data = {"name": "Naampje", "icon": "naampje", "color": "000000"}
    response = client.post(f"/v1/flavors", json=data, follow_redirects=True)
    assert response.status_code == 403
