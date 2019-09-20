def test_categories_list_endpoint(client):
    response = client.get(f"/v1/categories", follow_redirects=True)
    assert response.status_code == 403


def test_categories_create_endpoint(client, shop_1):
    data = {"name": "Naampje", "description": "Description", "shop_id": str(shop_1.id)}
    response = client.post(f"/v1/categories", json=data, follow_redirects=True)
    assert response.status_code == 403
