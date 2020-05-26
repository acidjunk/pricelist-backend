# from unittest import mock

from database import Order


def test_add_order(client, price_1, price_2, kind_1, kind_2, shop_with_products):
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
            "kind_name": kind_1.name,
            "internal_product_id": "02",
            "quantity": 1,
        },
    ]
    data = {
        "shop_id": str(shop_with_products.id),
        "total": 24.0,  # 2x 1 gram of 10,- + 1 joint of 4
        "order_info": items,
    }
    response = client.post(f"/v1/orders", json=data, follow_redirects=True)
    assert response.status_code == 201

    order = Order.query.first()
    assert order.shop_id == shop_with_products.id
    assert order.total == 24.0
    assert order.status == "pending"
    assert order.order_info == items


# def complete_order(client, kind_1):
#     # somehow check_quick_token() looses the request in test setup
#     with mock.patch("flask_security.decorators._check_token", return_value=True):
#         with mock.patch("flask_principal.Permission.can", return_value=True):
#
#             kind_id = str(uuid.uuid4())
#             kind = Kind(
#                 id=kind_id,
#                 name="Indica",
#                 c=False,
#                 h=False,
#                 i=True,
#                 s=False,
#                 short_description_nl="Short NL",
#                 description_nl="Description NL",
#                 short_description_en="Short NL",
#                 description_en="Description EN",
#             )
#             flavor = Flavor(id=str(uuid.uuid4()), name="Lemon")
#             db.session.add(kind)
#             db.session.add(flavor)
#             db.session.commit()
#
#
#
#
#             data = {"kind_id": str(kind.id), "flavor_id": str(flavor.id)}
#             response = client.post(f"/v1/kinds-to-flavors", json=data, follow_redirects=True)
#             assert response.status_code == 201
#
#             response = client.get(f"/v1/kinds-to-flavors", follow_redirects=True)
#             assert response.status_code == 200
#             json = response.json
#             assert len(json) == 1
