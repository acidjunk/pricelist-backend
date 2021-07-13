from datetime import datetime

import structlog
from apis.helpers import (
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
from database import Kind
from flask import request
from flask_restx import Namespace, Resource, fields, marshal_with, reqparse
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


delete_serializer = api.model("Kind", {"image": fields.String(required=True)})


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
    @marshal_with(image_serializer)
    def put(self, id):
        args = file_upload.parse_args()
        logger.warning("Ignoring files via args! (using JSON body)", args=args)
        item = load(Kind, id)
        # todo: raise 404 o abort

        data = request.get_json()

        kind_update = {}
        image_cols = ["image_1", "image_2", "image_3", "image_4", "image_5", "image_6"]
        for image_col in image_cols:
            if data.get(image_col) and type(data[image_col]) == dict:
                name = name_file(image_col, item.name, getattr(item, image_col))
                upload_file(data[image_col]["src"], name)  # todo: use mime-type in first part of
                kind_update[image_col] = name

        if kind_update:
            kind_update["complete"] = (
                True if data.get("image_1") and item.description_nl and item.description_en else False
            )
            kind_update["modified_at"] = datetime.utcnow()
            item = update(item, kind_update)

        return item, 201


@api.route("/delete/<id>")
@api.doc("Image delete operations.")
class KindImageDeleteResource(Resource):
    @api.expect(delete_serializer)
    @marshal_with(image_serializer)
    def put(self, id):
        image_cols = ["image_1", "image_2", "image_3", "image_4", "image_5", "image_6"]
        item = load(Kind, id)

        image = api.payload["image"]
        if image in image_cols:
            setattr(item, image, "")
            save(item)

        return item, 201
