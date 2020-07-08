def test_kinds_list_endpoint(client, kind_1):
    response = client.get(f"/v1/kinds", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
