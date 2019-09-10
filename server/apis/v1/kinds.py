import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, query_with_filters
from database import Kind
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("kinds", description="Kind related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

kind_marshaller = api.model(
    "Kind",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Product name"),
        "short_description_nl": fields.String(description="NL Description as shown in the price list"),
        "description_nl": fields.String(description="EN Description as shown in the detail view"),
        "short_description_en": fields.String(description="NL Description as shown in the price list"),
        "description_en": fields.String(description="EN Description as shown in the detail view"),
        "tags": fields.Nested(tag_fields),
        "flavors": fields.Nested(flavor_fields),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all kinds.")
class KindResourceList(Resource):
    @marshal_with(kind_marshaller)
    @api.doc(parser=parser)
    def get(self):
        """List (Product)Kinds"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(Kind, Kind.query, range, sort, "")
        # Todo: return items from selected shop/category
        for kind in query_result:
            kind.tags = [{"id": tag.tag.id, "name": tag.tag.name, "amount": tag.amount} for tag in kind.kind_to_tags]
            kind.flavors = [
                {
                    "id": flavor.flavor.id,
                    "name": flavor.flavor.name,
                    "icon": flavor.flavor.icon,
                    "color": flavor.flavor.color,
                }
                for flavor in kind.kind_to_flavors
            ]
        return query_result, 200, {"Content-Range": content_range}
