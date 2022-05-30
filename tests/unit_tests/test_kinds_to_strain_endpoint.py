import uuid
from unittest import mock
from server.database import Kind, Strain, db


def test_add_strain_to_kind(client):
    # somehow check_quick_token() looses the request in test setup
    with mock.patch("flask_security.decorators._check_token", return_value=True):
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
            strain = Strain(id=str(uuid.uuid4()), name="Haze")
            db.session.add(kind)
            db.session.add(strain)
            db.session.commit()

            data = {"kind_id": str(kind.id), "strain_id": str(strain.id)}
            response = client.post(f"/v1/kinds-to-strains", json=data, follow_redirects=True)
            assert response.status_code == 201

            response = client.get(f"/v1/kinds-to-strains", follow_redirects=True)
            assert response.status_code == 200
            json = response.json
            assert len(json) == 1
