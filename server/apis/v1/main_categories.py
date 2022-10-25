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
from database import MainCategory
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("main categories", description="Main category related operations")

main_category_serializer = api.model(
    "MainCategory",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="MainCategory name"),
        "name_en": fields.String(description="MainCategory name (EN)"),
        "shop_id": fields.String(required=True, description="Shop Id"),
    },
)

main_category_serializer_with_shop_names = {
    "id": fields.String(required=True),
    "name": fields.String(required=True, description="MainCategory name"),
    "name_en": fields.String(description="MainCategory name (EN)"),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "shop_name": fields.String(description="Shop Name"),
    "main_category_and_shop": fields.String(description="Category + shop name"),
}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("MainCategories list and create.")
class MainCategoryResourceList(Resource):
    @roles_accepted("admin", "employee")
    @marshal_with(main_category_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self):
        """List MainCategories"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(MainCategory, MainCategory.query, range, sort, filter)
        for result in query_result:
            result.shop_name = result.shop.name
            result.main_category_and_shop = f"{result.name} in {result.shop.name}"

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(main_category_serializer)
    @api.marshal_with(main_category_serializer)
    def post(self):
        """New MainCategory"""
        category = MainCategory(id=str(uuid.uuid4()), **api.payload)
        save(category)
        return category, 201


@api.route("/<id>")
@api.doc("MainCategory detail operations.")
class MainCategoryResource(Resource):
    @roles_accepted("admin", "employee")
    @marshal_with(main_category_serializer_with_shop_names)
    def get(self, id):
        """List MainCategory"""
        item = load(MainCategory, id)
        item.shop_name = item.shop.name
        item.category_and_shop = f"{item.shop.name}:{item.name}"
        return item, 200

    @roles_accepted("admin")
    @api.expect(main_category_serializer)
    @api.marshal_with(main_category_serializer)
    def put(self, id):
        """Edit MainCategory"""
        item = load(MainCategory, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete MainCategory"""
        item = load(MainCategory, id)
        delete(item)
        return "", 204
