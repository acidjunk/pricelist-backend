import uuid

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Category
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("categories", description="Category related operations")

category_serializer = api.model(
    "Category", {"id": fields.String(), "name": fields.String(required=True, description="Unique category name")}
)
category_serializer = api.model(
    "Category",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Category name"),
        "shop_id": fields.String(required=True, description="Shop Id"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all categories.")
class CategoryResourceList(Resource):
    @marshal_with(category_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List Categories"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(Category, Category.query, range, sort, "")
        return query_result, 200, {"Content-Range": content_range}

    @api.expect(category_serializer)
    @api.marshal_with(category_serializer)
    def post(self):
        """New Shops"""
        category = Category(id=str(uuid.uuid4()), **api.payload)
        save(category)
        return category, 201


@api.route("/<id>")
@api.doc("Category detail operations.")
class CategoryResource(Resource):
    @marshal_with(category_serializer)
    def get(self, id):
        """List Category"""
        item = load(Category, id)
        return item, 200

    @api.expect(category_serializer)
    @api.marshal_with(category_serializer)
    def put(self, id):
        """Edit Category"""
        item = load(Category, id)
        item = update(item, api.payload)
        return item, 201
