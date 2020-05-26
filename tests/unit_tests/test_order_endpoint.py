from unittest import mock

from database import Order


def test_order_list(client, shop_with_order):
    with mock.patch("flask_security.decorators._check_token", return_value=True):
        with mock.patch("flask_principal.Permission.can", return_value=True):

            response = client.get(f"/v1/orders", follow_redirects=True)
            assert response.status_code == 200
            assert len(response.json) == 2


def test_create_order(client, price_1, price_2, kind_1, kind_2, shop_with_products):
    items = [
        {
            "description": "1 gram",
            "price": price_1.one,
            "kind_id": str(kind_1.id),
            "kind_name": kind_1.name,
            "internal_product_id": "01",
            "quantity": 2,
        },
        {
            "description": "1 joint",
            "price": price_2.joint,
            "kind_id": str(kind_2.id),
            "kind_name": kind_2.name,
            "internal_product_id": "02",
            "quantity": 1,
        },
    ]
    data = {
        "shop_id": str(shop_with_products.id),
        "total": 24.0,  # 2x 1 gram of 10,- + 1 joint of 4
        "notes": "Nice one",
        "order_info": items,
    }
    response = client.post(f"/v1/orders", json=data, follow_redirects=True)
    assert response.status_code == 201
    assert response.json["customer_order_id"] == 1
    assert response.json["total"] == 24.0

    order = Order.query.filter_by(customer_order_id=1).first()
    assert order.shop_id == shop_with_products.id
    assert order.total == 24.0
    assert order.customer_order_id == 1
    assert order.notes == "Nice one"
    assert order.status == "pending"
    assert order.order_info == items

    # test with a second order to also cover the automatic increase of `customer_order_id`
    response = client.post(f"/v1/orders", json=data, follow_redirects=True)
    assert response.json["customer_order_id"] == 2
    assert response.json["total"] == 24.0

    assert response.status_code == 201
    order = Order.query.filter_by(customer_order_id=2).first()
    assert order.customer_order_id == 2


def test_create_order_validation(client, price_1, price_2, kind_1, kind_2, shop_with_products):
    items = [
        {
            "description": "1 gram",
            "price": price_1.one,
            "kind_id": str(kind_1.id),
            "kind_name": kind_1.name,
            "internal_product_id": "01",
            "quantity": 2,
        },
        {
            "description": "1 joint",
            "price": price_2.joint,
            "kind_id": str(kind_2.id),
            "kind_name": kind_2.name,
            "internal_product_id": "02",
            "quantity": 1,
        },
    ]
    # Wrong shop_id
    data = {
        "shop_id": "afda6a2f-293d-4d76-a4f9-1a2d08b56835",
        "total": 24.0,  # 2x 1 gram of 10,- + 1 joint of 4
        "notes": "Nice one",
        "order_info": items,
    }
    response = client.post(f"/v1/orders", json=data, follow_redirects=True)
    assert response.status_code == 404

    # No shop_id
    data = {"total": 24.0, "notes": "Nice one", "order_info": items}  # 2x 1 gram of 10,- + 1 joint of 4
    response = client.post(f"/v1/orders", json=data, follow_redirects=True)
    assert response.status_code == 400

    # Todo: test checksum functionality (totals should match with quantity in items)


def test_patch_order_to_complete(client, shop_with_order):
    # Get the uncompleted order_id from the fixture:
    order = Order.query.filter_by(status="pending").first()

    # somehow check_quick_token() looses the request in test setup
    with mock.patch("flask_security.decorators._check_token", return_value=True):
        with mock.patch("flask_principal.Permission.can", return_value=True):

            data = {"status": "complete"}
            response = client.patch(f"/v1/orders/{order.id}", json=data, follow_redirects=True)
            assert response.status_code == 204

            updated_order = Order.query.filter_by(id=str(order.id)).first()
            assert updated_order.status == "complete"
            assert updated_order.completed_at is not None
