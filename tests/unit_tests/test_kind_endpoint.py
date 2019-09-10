def test_kinds_endpoint(client, tag_1):
    response = client.get(f"/v1/kinds", follow_redirects=True)
    assert response.status_code == 200


# def test_kinds_endpoint_auth(client, tag_1):
#     response = client.get(f'/v1/kinds', follow_redirects=True)
#     assert response.status_code == 401
