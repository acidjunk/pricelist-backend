from datetime import datetime

import structlog
from server.apis.helpers import (
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    name_file,
    query_with_filters,
    save,
    update,
    upload_file,
)
from server.database import Category
from flask import request
from flask_restx import Namespace, Resource, fields, marshal_with, reqparse
from flask_security import roles_accepted
from werkzeug.datastructures import FileStorage

logger = structlog.get_logger(__name__)

api = Namespace("categories-images", description="Category image related operations")

image_serializer = api.model(
    "Category",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True),
        "shop_id": fields.String(required=True),
        "image_1": fields.String(required=True, description="File Name 1"),
        "image_2": fields.String(required=True, description="File Name 2"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")

file_upload = reqparse.RequestParser()
file_upload.add_argument("image_1", type=FileStorage, location="files", help="image_1")
file_upload.add_argument("image_2", type=FileStorage, location="files", help="image_2")

delete_serializer = api.model("Category", {"image": fields.String(required=True)})


@api.route("/")
@api.doc("Show all category images.")
class CategoryImageResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List all product category images"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(
            Category, Category.query, range, sort, filter, quick_search_columns=["name", "image_1", "image_2"]
        )

        return query_result, 200, {"Content-Range": content_range}


@api.route("/<id>")
@api.doc("Image detail operations.")
class CategoryImageResource(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    def get(self, id):
        """List Image"""
        item = load(Category, id)
        return item, 200

    @api.expect(file_upload)
    @marshal_with(image_serializer)
    def put(self, id):
        args = file_upload.parse_args()
        logger.warning("Ignoring files via args! (using JSON body)", args=args)
        item = load(Category, id)
        # todo: raise 404 o abort

        data = request.get_json()

        category_update = {}
        image_cols = ["image_1", "image_2"]
        for image_col in image_cols:
            if data.get(image_col) and type(data[image_col]) == dict:
                name = name_file(image_col, item.name, getattr(item, image_col))
                upload_file(data[image_col]["src"], name)  # todo: use mime-type in first part of
                category_update[image_col] = name

        if category_update:
            category_update["shop_id"] = item.shop_id
            item = update(item, category_update)

        return item, 201


@api.route("/delete/<id>")
@api.doc("Image delete operations.")
class CategoryImageDeleteResource(Resource):
    @api.expect(delete_serializer)
    @marshal_with(image_serializer)
    def put(self, id):
        image_cols = ["image_1", "image_2"]
        item = load(Category, id)

        image = api.payload["image"]
        if image in image_cols:
            setattr(item, image, "")
            save(item)

        return item, 201
