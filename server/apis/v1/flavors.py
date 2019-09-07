import uuid

import structlog
from database import Flavor, db
from flask_restplus import Namespace, Resource, abort, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("flavors", description="Flavor related operations")

flavor_serializer = api.model(
    "Flavor",
    {
        "id": fields.String(),
        "name": fields.String(required=True, description="Unique flavor name"),
        "icon": fields.String(required=True, description="Unique flavor icon"),
        "color": fields.String(description="Hex color digits"),
    },
)


@api.route("/")
@api.doc("Show all flavors.")
class FlavorResourceList(Resource):
    @marshal_with(flavor_serializer)
    def get(self):
        """List Flavors"""
        return Flavor.query.all()

    @api.expect(flavor_serializer)
    @api.marshal_with(flavor_serializer, code=201)
    def post(self):
        """New Flavors"""
        # Todo: generate UUID from backend
        flavor = Flavor(id=str(uuid.uuid4()), **api.payload)
        try:
            db.session.add(flavor)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            abort(400, "DB error: {}".format(str(error)))
        return 201
