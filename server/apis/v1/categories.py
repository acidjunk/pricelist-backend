import uuid

import structlog
from apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    query_with_filters,
    save,
    update,
)
from database import Category
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("categories", description="Category related operations")

category_serializer = api.model(
    "Category",
    {
        "id": fields.String(required=True),
        "order_number": fields.Integer(),
        "name": fields.String(required=True, description="Category name"),
        "name_en": fields.String(required=False, description="Category name (EN)"),
        "icon": fields.String(required=True, description="Unique flavor icon"),
        "color": fields.String(description="Hex color digits"),
        "shop_id": fields.String(required=True, description="Shop Id"),
        "cannabis": fields.Boolean(required=True, description="Will this category be used to store cannabis products?"),
    },
)

category_serializer_with_shop_names = {
    "id": fields.String(required=True),
    "order_number": fields.Integer(),
    "name": fields.String(required=True, description="Category name"),
    "name_en": fields.String(required=False, description="Category name (EN)"),
    "main_category_id": fields.String(description="Main category name"),
    "icon": fields.String(required=True, description="Unique flavor icon"),
    "color": fields.String(description="Hex color digits"),
    "main_category_name": fields.String(description="Main category name"),
    "main_category_name_en": fields.String(description="Main category name (EN)"),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "shop_name": fields.String(description="Shop Name"),
    "category_and_shop": fields.String(description="Category + shop name"),
    "cannabis": fields.Boolean(description="Will this category be used to store cannabis products?"),
}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all categories.")
class CategoryResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(category_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self):
        """List Categories"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Category, Category.query, range, sort, filter)
        for result in query_result:
            result.main_category_name = result.main_category.name if result.main_category else "Unknown"
            result.main_category_name_en = result.main_category.name_en if result.main_category else "Unknown"
            result.shop_name = result.shop.name
            result.category_and_shop = f"{result.name} in {result.shop.name}"

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(category_serializer)
    @api.marshal_with(category_serializer)
    def post(self):
        """New Category"""
        category = Category(id=str(uuid.uuid4()), **api.payload)
        save(category)
        return category, 201


@api.route("/<id>")
@api.doc("Category detail operations.")
class CategoryResource(Resource):
    @roles_accepted("admin")
    @marshal_with(category_serializer_with_shop_names)
    def get(self, id):
        """List Category"""
        item = load(Category, id)
        item.shop_name = item.shop.name
        item.category_and_shop = f"{item.name} in {item.shop.name}"
        item.main_category_name = item.main_category.name if item.main_category else "Unknown"
        item.main_category_name_en = item.main_category.name_en if item.main_category else "Unknown"
        return item, 200

    @roles_accepted("admin")
    @api.expect(category_serializer)
    @api.marshal_with(category_serializer)
    def put(self, id):
        """Edit Category"""
        item = load(Category, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete Category"""
        item = load(Category, id)
        delete(item)
        return "", 204
