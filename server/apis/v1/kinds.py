import uuid

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Kind
from flask_restplus import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("kinds", description="Kind related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

kind_serializer = api.model(
    "Kind",
    {
        "id": fields.String(),
        "name": fields.String(required=True, description="Product name"),
        "short_description_nl": fields.String(description="NL Description as shown in the price list"),
        "description_nl": fields.String(description="EN Description as shown in the detail view"),
        "short_description_en": fields.String(description="NL Description as shown in the price list"),
        "description_en": fields.String(description="EN Description as shown in the detail view"),
        "c": fields.Boolean(description="CBD?"),
        "h": fields.Boolean(description="Hybrid?"),
        "i": fields.Boolean(description="Indica?"),
        "s": fields.Boolean(description="Sativa?"),
    },
)

kind_serializer_with_relations = {
    "id": fields.String(),
    "name": fields.String(required=True, description="Product name"),
    "short_description_nl": fields.String(description="NL Description as shown in the price list"),
    "description_nl": fields.String(description="EN Description as shown in the detail view"),
    "short_description_en": fields.String(description="NL Description as shown in the price list"),
    "description_en": fields.String(description="EN Description as shown in the detail view"),
    "c": fields.Boolean(description="CBD?"),
    "h": fields.Boolean(description="Hybrid?"),
    "i": fields.Boolean(description="Indica?"),
    "s": fields.Boolean(description="Sativa?"),
    "tags": fields.Nested(tag_fields),
    "flavors": fields.Nested(flavor_fields),
}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all kinds.")
class KindResourceList(Resource):
    @marshal_with(kind_serializer_with_relations)
    @api.doc(parser=parser)
    def get(self):
        """List (Product)Kinds"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(Kind, Kind.query, range, sort, "")
        # Todo: return items from selected shop/category
        for kind in query_result:
            kind.tags = [
                {"id": tag.id, "name": f"{tag.tag.name}: {tag.amount}", "amount": tag.amount}
                for tag in kind.kind_to_tags
            ]
            kind.flavors = [
                {"id": flavor.id, "name": flavor.flavor.name, "icon": flavor.flavor.icon, "color": flavor.flavor.color}
                for flavor in kind.kind_to_flavors
            ]
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(kind_serializer)
    @api.marshal_with(kind_serializer)
    def post(self):
        """New Shops"""
        kind = Kind(id=str(uuid.uuid4()), **api.payload)
        save(kind)
        return kind, 201


@api.route("/<id>")
@api.doc("Kind detail operations.")
class KindResource(Resource):
    @marshal_with(kind_serializer_with_relations)
    def get(self, id):
        """List Kind"""
        item = load(Kind, id)
        item.tags = [{"id": tag.id, "name": tag.tag.name, "amount": tag.amount} for tag in item.kind_to_tags]
        item.flavors = [
            {"id": flavor.id, "name": flavor.flavor.name, "icon": flavor.flavor.icon, "color": flavor.flavor.color}
            for flavor in item.kind_to_flavors
        ]
        return item, 200

    @roles_accepted("admin")
    @api.expect(kind_serializer)
    @api.marshal_with(kind_serializer)
    def put(self, id):
        """Edit Kind"""
        item = load(Kind, id)
        item = update(item, api.payload)
        return item, 201
