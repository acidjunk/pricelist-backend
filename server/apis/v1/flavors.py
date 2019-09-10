import uuid

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, query_with_filters
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

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all flavors.")
class FlavorResourceList(Resource):
    @marshal_with(flavor_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List Flavors"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(Flavor, Flavor.query, range, sort, "")
        # query_result, content_range = _flavor_query_with_filters(Flavor.query)
        return query_result, 200, {"Content-Range": content_range}

    @api.expect(flavor_serializer)
    @api.marshal_with(flavor_serializer, code=201)
    def post(self):
        """New Flavors"""
        flavor = Flavor(id=str(uuid.uuid4()), **api.payload)
        try:
            db.session.add(flavor)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            abort(400, "DB error: {}".format(str(error)))
        return 201
