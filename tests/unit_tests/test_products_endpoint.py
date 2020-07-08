def test_products_list_endpoint(client, product_1):
    response = client.get(f"/v1/products", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
