import uuid

import structlog
from database import Tag, db
from flask_restplus import Namespace, Resource, abort, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("tags", description="Tag related operations")

tag_serializer = api.model(
    "Tag", {"id": fields.String(), "name": fields.String(required=True, description="Unique tag name")}
)


@api.route("/")
@api.doc("Show all tags.")
class TagResourceList(Resource):
    @marshal_with(tag_serializer)
    def get(self):
        """List Tags"""
        return Tag.query.all()

    @api.expect(tag_serializer)
    @api.marshal_with(tag_serializer, code=201)
    def post(self):
        """New Tags"""
        # Todo: generate UUID from backend
        tag = Tag(id=str(uuid.uuid4()), **api.payload)
        try:
            db.session.add(tag)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            abort(400, "DB error: {}".format(str(error)))
        return 201
