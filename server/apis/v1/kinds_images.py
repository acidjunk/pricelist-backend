import os

import structlog
from apis.helpers import (
    get_range_from_args, get_sort_from_args, load, query_with_filters, update,
    get_filter_from_args, save
)
from database import Kind
from flask import current_app
from flask_restplus import Namespace, Resource, abort, fields, marshal_with, reqparse
from flask_security import roles_accepted
from werkzeug.datastructures import FileStorage

logger = structlog.get_logger(__name__)

api = Namespace("kinds-images", description="Product-kind image related operations")

image_serializer = api.model(
    "Kind",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True),
        "image_1": fields.String(required=True, description="File Name 1"),
        "image_2": fields.String(required=True, description="File Name 2"),
        "image_3": fields.String(required=True, description="File Name 3"),
        "image_4": fields.String(required=True, description="File Name 4"),
        "image_5": fields.String(required=True, description="File Name 5"),
        "image_6": fields.String(required=True, description="File Name 6"),
    },
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")

file_upload = reqparse.RequestParser()
file_upload.add_argument("image_1", type=FileStorage, location="files", help="image_1")
file_upload.add_argument("image_2", type=FileStorage, location="files", help="image_2")
file_upload.add_argument("image_3", type=FileStorage, location="files", help="image_3")
file_upload.add_argument("image_4", type=FileStorage, location="files", help="image_4")
file_upload.add_argument("image_5", type=FileStorage, location="files", help="image_5")
file_upload.add_argument("image_6", type=FileStorage, location="files", help="image_6")


@api.route("/")
@api.doc("Show all product kind images.")
class KindImageResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List all product kind images"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(
            Kind,
            Kind.query,
            range,
            sort,
            filter,
            quick_search_columns=["name", "image_1", "image_2", "image_3", "image_4", "image_5", "image_6"],
        )
        # for result in query_result:
        #     result.shop_name = result.shop.name
        #     result.image_and_shop = f"{result.shop.name}:{result.name}"

        return query_result, 200, {"Content-Range": content_range}


@api.route("/<id>")
@api.doc("Image detail operations.")
class KindImageResource(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    def get(self, id):
        """List Image"""
        item = load(Kind, id)
        return item, 200

    @api.expect(file_upload)
    def put(self, id):
        args = file_upload.parse_args()
        print(args)
        item = load(Kind, id)
        if args["image_1"].mimetype == "application/png" or 1:
            destination = os.path.join(current_app.config.get("DATA_FOLDER", "data"), "medias/")
            if not os.path.exists(destination):
                os.makedirs(destination)
            png_file = "%s%s" % (destination, "custom_file_name.png")
            args["file"].save(png_file)
            item.image_1 = "custom_file_name"
            save(item)
            return item, 201
        else:
            abort(404)
        return {"status": "Done"}
