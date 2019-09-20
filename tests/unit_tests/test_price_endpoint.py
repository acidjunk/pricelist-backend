def test_prices_list_endpoint(client, price_1):
    response = client.get(f"/v1/prices", follow_redirects=True)
    assert response.status_code == 403


def test_prices_create_endpoint(client):
    data = {"internal_product_id": 5, "one": 10.1, "five": 0.43}
    response = client.post(f"/v1/prices", json=data, follow_redirects=True)
    assert response.status_code == 403
