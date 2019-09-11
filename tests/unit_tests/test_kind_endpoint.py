import uuid

from database import Flavor, Kind, Tag, db


def test_kinds_list_endpoint(client, kind_1):
    response = client.get(f"/v1/kinds", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1


def test_add_tag_to_kind(client):
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
    response = client.post(f"/v1/kinds/tags", json=data, follow_redirects=True)
    assert response.status_code == 201

    response = client.get(f"/v1/kinds/{kind_id}/tags", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1


def test_add_flavor_to_kind(client):
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
    flavor = Flavor(id=str(uuid.uuid4()), name="Lemon")
    db.session.add(kind)
    db.session.add(flavor)
    db.session.commit()

    data = {"kind_id": str(kind.id), "flavor_id": str(flavor.id)}
    response = client.post(f"/v1/kinds/flavors", json=data, follow_redirects=True)
    assert response.status_code == 201

    response = client.get(f"/v1/kinds/{kind_id}/flavors", follow_redirects=True)
    assert response.status_code == 200
    json = response.json
    assert len(json) == 1
