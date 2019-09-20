import uuid

from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Flavor, Kind, KindToFlavor
from flask_restplus import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

api = Namespace("kinds-to-flavors", description="Kind to flavor related operations")

kind_to_flavor_serializer = api.model(
    "KindToFlavor",
    {
        "id": fields.String(),
        "flavor_id": fields.String(required=True, description="Flavor Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("KindsToFlavos")
class KindsToFlavorsResourceList(Resource):
    @marshal_with(kind_to_flavor_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List flavors for a product kind"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "id")

        query_result, content_range = query_with_filters(KindToFlavor, KindToFlavor.query, range, sort, "")
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(kind_to_flavor_serializer)
    @api.marshal_with(kind_to_flavor_serializer)
    def post(self):
        """New KindToFlavor"""
        flavor = Flavor.query.filter(Flavor.id == api.payload["flavor_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()

        if not flavor or not kind:
            abort(400, "Flavor or kind not found")

        check_query = KindToFlavor.query.filter_by(kind_id=kind.id).filter_by(flavor_id=flavor.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        kind_to_flavor = KindToFlavor(id=str(uuid.uuid4()), kind=kind, flavor=flavor)
        save(kind_to_flavor)
        return kind_to_flavor, 201


@api.route("/<id>")
@api.doc("KindToFlavor detail operations.")
class KindsToFlavorsResource(Resource):
    @roles_accepted("admin")
    @marshal_with(kind_to_flavor_serializer)
    def get(self, id):
        """List KindToFlavor"""
        item = load(KindToFlavor, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(kind_to_flavor_serializer)
    @api.marshal_with(kind_to_flavor_serializer)
    def put(self, id):
        """Edit KindToFlavor"""
        item = load(KindToFlavor, id)
        item = update(item, api.payload)
        return item, 201