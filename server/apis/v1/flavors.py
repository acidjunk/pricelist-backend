import uuid

import structlog
from apis.helpers import _flavor_query_with_filters
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
parser.add_argument("range", location="args", help="Pagination")
parser.add_argument("filter", location="args", help="Filter list options")
parser.add_argument("sort", location="args", help="Sort list options")


@api.route("/")
@api.doc("Show all flavors.")
class FlavorResourceList(Resource):
    @marshal_with(flavor_serializer)
    def get(self):
        """List Flavors"""
        args = parser.parse_args()
        range = []
        if args["range"]:
            try:
                input = args["range"][1:-1].split(",")
                for i in input:
                    range.append(int(i))
            except:
                range = [0, 19]
            logger.info("Query parameters", range=range)

        sort = []
        if args["sort"]:
            try:
                input = args["sort"].split(",")
                sort.append(input[0][2:-1])
                sort.append(input[1][1:-2])
            except:
                sort = []
            logger.info("Query parameters", sort=sort)

        query_result, content_range = _flavor_query_with_filters(Flavor.query, range, sort, "")
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
