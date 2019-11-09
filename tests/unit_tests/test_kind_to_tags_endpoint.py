import uuid
from unittest import mock

from database import Kind, Tag, db


def test_add_tag_to_kind(client):
    # @Guido: This tests shouldn't need:
    # - the manual setup of a Kind and a Tag
    #   (I've fixtures for them but they don't seem to work ok
    # - the mock patch for simulated user login.
    #   (I've a fixture for a user shop_admin that works fine for account tests, like `test_shop_login()`)

    with mock.patch("flask_principal.Permission.can", return_value=True):
        kind_id = str(uuid.uuid4())
        kind = Kind(
            id=kind_id,
            name="Indica",
            c=False,
            h=False,
            i=True,
            s=False,
            short_description_nl="Short NL",
            description_nl="Description NL",
            short_description_en="Short NL",
            description_en="Description EN",
        )
        tag = Tag(id=str(uuid.uuid4()), name="Gigly")
        db.session.add(kind)
        db.session.add(tag)
        db.session.commit()

        data = {"kind_id": str(kind.id), "tag_id": str(tag.id), "amount": 60}
        response = client.post(f"/v1/kinds-to-tags", json=data, follow_redirects=True)
        assert response.status_code == 201

        response = client.get(f"/v1/kinds-to-tags", follow_redirects=True)
        assert response.status_code == 200
        json = response.json
        assert len(json) == 1


def test_add_tag_to_kind_with_fixtures(shop_admin_logged_in, kind_1, tag_1):
    data = {"kind_id": str(kind_1.id), "tag_id": str(tag_1.id), "amount": 60}

    response = shop_admin_logged_in.post(f"/v1/kinds-to-tags", json=data, follow_redirects=True)
    assert response.status_code == 201

    response = shop_admin_logged_in.get(f"/v1/kinds-to-tags", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
